"""
Meeting Model

Stores meeting transcripts, notes, and action items.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Enum
from sqlalchemy.sql import func
import enum

from app.database import Base


class MeetingStatus(str, enum.Enum):
    """Meeting status enumeration."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MeetingMode(str, enum.Enum):
    """Meeting agent mode."""
    SILENT = "silent"           # Just record and take notes
    REPRESENT = "represent"     # Can speak on behalf of user
    ASSIST = "assist"           # Sends suggestions via Telegram


class Meeting(Base):
    """Meeting model for storing transcripts and notes."""
    
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    title = Column(String(255), nullable=False)
    meeting_url = Column(String(500), nullable=True)
    platform = Column(String(50), default="google_meet")  # google_meet, zoom, teams
    
    # Timing
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    
    # Status and mode
    status = Column(
        Enum(MeetingStatus),
        default=MeetingStatus.SCHEDULED
    )
    mode = Column(
        Enum(MeetingMode),
        default=MeetingMode.SILENT
    )
    
    # Content
    transcript = Column(JSON, nullable=True)  # Full transcript with timestamps
    """
    Transcript format:
    [
        {"timestamp": "00:01:23", "speaker": "John", "text": "Hello everyone"},
        {"timestamp": "00:01:30", "speaker": "Jane", "text": "Hi John"},
        ...
    ]
    """
    
    notes = Column(JSON, nullable=True)  # Structured notes from Claude
    """
    Notes format:
    {
        "summary": "...",
        "key_points": ["...", "..."],
        "decisions": [{"decision": "...", "rationale": "..."}],
        "questions": ["..."]
    }
    """
    
    action_items = Column(JSON, nullable=True)
    """
    Action items format:
    [
        {"task": "...", "assigned_to": "...", "deadline": "...", "priority": "high"},
        ...
    ]
    """
    
    # Participants
    participants = Column(JSON, nullable=True)  # List of participant names
    
    # Language
    language = Column(String(10), default="en")  # en, fr, ar
    
    # Recording
    recording_url = Column(String(500), nullable=True)
    
    # Raw transcript text (for quick access)
    raw_transcript = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Meeting(id={self.id}, title='{self.title}', status={self.status})>"
