"""
User Model

Stores user profile and communication preferences.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    """User profile model."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Identity
    user_id = Column(String(255), unique=True, index=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=True)
    telegram_chat_id = Column(String(50), nullable=True)
    
    # Communication style (learned from user's messages)
    communication_style = Column(JSON, nullable=True)
    """
    Communication style format:
    {
        "tone": "professional",  # professional, casual, friendly
        "emoji_frequency": "occasional",  # never, rare, occasional, frequent
        "avg_message_length": 50,
        "common_phrases": ["On it!", "Let me check", "Sounds good"],
        "formality_by_contact": {
            "boss@email.com": "formal",
            "friend@email.com": "casual"
        }
    }
    """
    
    # Preferences
    preferences = Column(JSON, nullable=True)
    """
    Preferences format:
    {
        "default_language": "en",
        "meeting_notification_minutes": 10,
        "auto_approve_low_priority": false,
        "approval_timeout_seconds": 300
    }
    """
    
    # Integration tokens (encrypted in production)
    integrations = Column(JSON, nullable=True)
    """
    Integrations format:
    {
        "google": {"access_token": "...", "refresh_token": "..."},
        "slack": {"access_token": "...", "workspace_id": "..."},
        "github": {"access_token": "..."}
    }
    """
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_active = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, display_name='{self.display_name}')>"
