"""
Message Model

Stores messages and draft responses across platforms.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Enum, ForeignKey
from sqlalchemy.sql import func
import enum

from app.database import Base


class Platform(str, enum.Enum):
    """Communication platform."""
    SLACK = "slack"
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    TELEGRAM = "telegram"
    DISCORD = "discord"


class Urgency(str, enum.Enum):
    """Message urgency level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ApprovalStatus(str, enum.Enum):
    """Draft approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    EXPIRED = "expired"


class Message(Base):
    """Message model for tracking communications."""
    
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Platform info
    platform = Column(Enum(Platform), nullable=False)
    platform_message_id = Column(String(255), nullable=True)  # Original message ID
    
    # Participants
    sender = Column(String(255), nullable=False)
    recipient = Column(String(255), nullable=True)
    channel = Column(String(255), nullable=True)  # Slack channel, email thread, etc.
    
    # Content
    content = Column(Text, nullable=False)
    thread_id = Column(String(255), nullable=True)
    
    # Analysis
    urgency = Column(Enum(Urgency), default=Urgency.MEDIUM)
    language = Column(String(10), default="en")
    intent = Column(String(100), nullable=True)  # question, request, info, etc.
    
    # Draft response
    draft_response = Column(Text, nullable=True)
    draft_reasoning = Column(Text, nullable=True)  # Why JARVIS drafted this
    approval_status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    approved_at = Column(DateTime, nullable=True)
    
    # User modification (for learning)
    user_modified_response = Column(Text, nullable=True)
    
    # Timing
    received_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Message(id={self.id}, platform={self.platform}, sender='{self.sender}')>"
