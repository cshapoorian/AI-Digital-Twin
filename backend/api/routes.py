"""
API routes for the AI Digital Twin backend.

Endpoints:
- POST /chat - Send message and get AI response
- POST /feedback - Submit feedback for model improvement
- GET /health - Health check and status
"""

import os
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.models import (
    ChatRequest, ChatResponse,
    FeedbackRequest, FeedbackResponse,
    AnalyticsRequest, AnalyticsResponse,
    HealthResponse,
    AdminFeedbackItem, AdminFeedbackListResponse, AdminReviewResponse
)
from db import get_db, Conversation, Message, Feedback, Analytics
from core import generate_response

router = APIRouter()


def is_chat_enabled() -> bool:
    """Check if chat is enabled via environment variable (kill switch)."""
    return os.getenv("CHAT_ENABLED", "true").lower() == "true"


def verify_admin_key(key: str):
    """
    Verify the admin key for feedback digest access.

    Requires ADMIN_KEY to be set in the environment - if it's not
    configured, the admin endpoints are disabled entirely (404) rather
    than accepting any key.
    """
    admin_key = os.getenv("ADMIN_KEY")
    if not admin_key:
        raise HTTPException(status_code=404, detail="Not found")
    if not key or not secrets.compare_digest(key, admin_key):
        raise HTTPException(status_code=403, detail="Invalid admin key")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Process a chat message and return AI response.

    The endpoint:
    1. Checks if chat is enabled (kill switch)
    2. Gets or creates conversation in database
    3. Generates response using AI pipeline
    4. Stores messages in database
    5. Logs feedback if uncertainty detected
    """
    # Check kill switch
    if not is_chat_enabled():
        return ChatResponse(
            response="Chat is temporarily unavailable. Please check back later!",
            conversation_id=request.conversation_id,
            metadata={"maintenance": True}
        )

    # Get or create conversation
    conversation = db.query(Conversation).filter(
        Conversation.id == request.conversation_id
    ).first()

    if not conversation:
        conversation = Conversation(id=request.conversation_id)
        db.add(conversation)
        db.commit()

    # Build conversation history from database or request
    history = []
    if request.history:
        history = [{"role": m.role, "content": m.content} for m in request.history]
    else:
        # Load from database
        db_messages = db.query(Message).filter(
            Message.conversation_id == request.conversation_id
        ).order_by(Message.created_at).limit(20).all()
        history = [{"role": m.role, "content": m.content} for m in db_messages]

    # Generate response
    try:
        response_text, metadata = generate_response(
            user_message=request.message,
            conversation_history=history
        )
    except Exception as e:
        print(f"Pipeline error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating a response"
        )

    # Store messages in database
    user_msg = Message(
        conversation_id=request.conversation_id,
        role="user",
        content=request.message
    )
    assistant_msg = Message(
        conversation_id=request.conversation_id,
        role="assistant",
        content=response_text
    )
    db.add(user_msg)
    db.add(assistant_msg)

    # Auto-log feedback if uncertainty detected
    if metadata.get("uncertainty_detected"):
        feedback = Feedback(
            conversation_id=request.conversation_id,
            user_message=request.message,
            assistant_response=response_text,
            feedback_type="unanswered",
            notes="Auto-logged: Model expressed uncertainty"
        )
        db.add(feedback)

    db.commit()

    return ChatResponse(
        response=response_text,
        conversation_id=request.conversation_id,
        metadata=metadata
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    """
    Submit feedback about an interaction.

    Used to log:
    - Questions the model couldn't answer
    - Inappropriate responses
    - Inaccurate information
    - Thumbs up/down ratings with optional notes
    """
    feedback = Feedback(
        conversation_id=request.conversation_id,
        user_message=request.user_message,
        assistant_response=request.assistant_response,
        feedback_type=request.feedback_type,
        rating=request.rating,
        notes=request.notes
    )
    db.add(feedback)

    # Also log as analytics event
    analytics = Analytics(
        event_type="feedback",
        session_id=request.conversation_id,
        event_data=f'{{"type": "{request.feedback_type}", "rating": "{request.rating or "none"}"}}'
    )
    db.add(analytics)

    db.commit()
    db.refresh(feedback)

    return FeedbackResponse(success=True, feedback_id=feedback.id)


@router.post("/analytics", response_model=AnalyticsResponse)
async def track_event(request: AnalyticsRequest, db: Session = Depends(get_db)):
    """
    Track an analytics event (visit, message, etc.).
    Privacy-friendly: no personal data stored.
    """
    import json
    analytics = Analytics(
        event_type=request.event_type,
        session_id=request.session_id,
        event_data=json.dumps(request.metadata) if request.metadata else None
    )
    db.add(analytics)
    db.commit()

    return AnalyticsResponse(success=True)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns current status and whether chat is enabled.
    Useful for monitoring and the frontend kill switch check.
    """
    return HealthResponse(
        status="healthy",
        chat_enabled=is_chat_enabled(),
        timestamp=datetime.now(timezone.utc)
    )


@router.get("/admin/feedback", response_model=AdminFeedbackListResponse)
async def get_feedback_digest(
    key: str = Query(..., description="Admin key"),
    unreviewed_only: bool = Query(True, description="Only show unreviewed entries"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Feedback digest for the site owner.

    Surfaces questions the twin couldn't answer (or answered poorly) so
    they can be turned into new training data. Requires ADMIN_KEY.
    """
    verify_admin_key(key)

    query = db.query(Feedback)
    if unreviewed_only:
        query = query.filter(Feedback.reviewed == False)  # noqa: E712

    total = db.query(Feedback).count()
    unreviewed = db.query(Feedback).filter(Feedback.reviewed == False).count()  # noqa: E712

    items = query.order_by(Feedback.created_at.desc()).limit(limit).all()

    return AdminFeedbackListResponse(
        total=total,
        unreviewed=unreviewed,
        items=[AdminFeedbackItem.model_validate(item, from_attributes=True) for item in items]
    )


@router.post("/admin/feedback/{feedback_id}/review", response_model=AdminReviewResponse)
async def mark_feedback_reviewed(
    feedback_id: int,
    key: str = Query(..., description="Admin key"),
    db: Session = Depends(get_db)
):
    """Mark a feedback entry as reviewed. Requires ADMIN_KEY."""
    verify_admin_key(key)

    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback entry not found")

    feedback.reviewed = True
    db.commit()

    return AdminReviewResponse(success=True, feedback_id=feedback_id)
