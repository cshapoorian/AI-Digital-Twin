"""
SQLAlchemy models for the AI Digital Twin database.

Tables:
- Conversation: Chat sessions (identified by UUID)
- Message: Individual messages within a conversation
- Feedback: User feedback for model improvement
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


class Conversation(Base):
    """
    Represents a chat session.
    Each conversation has a unique ID (UUID from frontend) and tracks timestamps.
    """
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True)  # UUID format
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationship to messages
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")

    def __repr__(self):
        return f"<Conversation(id={self.id})>"


class Message(Base):
    """
    Individual message within a conversation.
    Stores the role (user/assistant) and message content.
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(10), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # Relationship to conversation
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role})>"


class Feedback(Base):
    """
    Feedback entries for model improvement.
    Tracks questions the model couldn't answer or answered poorly.
    Owner can review these to improve training data.
    """
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), nullable=True)  # Optional link to conversation
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=True)
    feedback_type = Column(String(20), nullable=False)  # 'unanswered', 'inappropriate', 'inaccurate'
    notes = Column(Text, nullable=True)  # Additional context
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Feedback(id={self.id}, type={self.feedback_type})>"
