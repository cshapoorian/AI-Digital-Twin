"""
Pydantic models for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class MessageItem(BaseModel):
    """Individual message in conversation history."""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1, max_length=5000)


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    message: str = Field(..., min_length=1, max_length=2000, description="User's message")
    conversation_id: str = Field(..., min_length=1, max_length=36, description="Session ID (UUID)")
    history: Optional[List[MessageItem]] = Field(
        default=None,
        max_length=50,
        description="Previous messages for context"
    )


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""
    response: str = Field(..., description="AI's response")
    conversation_id: str = Field(..., description="Session ID")
    metadata: Optional[dict] = Field(
        default=None,
        description="Additional info (uncertainty, blocked, etc.)"
    )


class FeedbackRequest(BaseModel):
    """Request body for feedback endpoint."""
    conversation_id: Optional[str] = Field(None, description="Related conversation ID")
    user_message: str = Field(..., min_length=1, max_length=2000)
    assistant_response: Optional[str] = Field(None, max_length=5000)
    feedback_type: str = Field(
        ...,
        pattern="^(unanswered|inappropriate|inaccurate|helpful|unhelpful|other)$",
        description="Type of feedback"
    )
    rating: Optional[str] = Field(
        None,
        pattern="^(positive|negative)$",
        description="Thumbs up (positive) or down (negative)"
    )
    notes: Optional[str] = Field(None, max_length=1000, description="Additional context")


class FeedbackResponse(BaseModel):
    """Response body for feedback endpoint."""
    success: bool
    feedback_id: int


class AnalyticsRequest(BaseModel):
    """Request body for analytics tracking."""
    event_type: str = Field(..., pattern="^(visit|message|feedback)$")
    session_id: Optional[str] = Field(None, max_length=36)
    metadata: Optional[dict] = Field(None, description="Extra event data")


class AnalyticsResponse(BaseModel):
    """Response body for analytics tracking."""
    success: bool


class HealthResponse(BaseModel):
    """Response body for health check."""
    status: str
    chat_enabled: bool
    timestamp: datetime
