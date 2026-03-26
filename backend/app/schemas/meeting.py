"""
Meeting Schemas

Pydantic models for meeting API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """Action item from a meeting."""
    task: str
    assigned_to: Optional[str] = "Unassigned"
    deadline: Optional[str] = "Not specified"
    priority: str = "medium"


class Decision(BaseModel):
    """Decision made in a meeting."""
    decision: str
    rationale: Optional[str] = None
    impact: Optional[str] = None


class MeetingNotes(BaseModel):
    """Structured meeting notes."""
    summary: str
    key_points: List[str] = []
    decisions: List[Decision] = []
    action_items: List[ActionItem] = []
    questions: List[str] = []
    next_steps: Optional[str] = None


class TranscriptSegment(BaseModel):
    """A segment of the transcript."""
    timestamp: str
    speaker: Optional[str] = None
    text: str


# Request/Response Models

class MeetingCreate(BaseModel):
    """Request model for creating a meeting."""
    title: str = Field(..., min_length=1, max_length=255)
    meeting_url: Optional[str] = None
    platform: str = "google_meet"
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    mode: str = "silent"  # silent, represent, assist
    language: str = "en"


class MeetingUpdate(BaseModel):
    """Request model for updating a meeting."""
    title: Optional[str] = None
    status: Optional[str] = None
    transcript: Optional[List[TranscriptSegment]] = None
    raw_transcript: Optional[str] = None
    notes: Optional[MeetingNotes] = None
    action_items: Optional[List[ActionItem]] = None
    participants: Optional[List[str]] = None


class MeetingResponse(BaseModel):
    """Response model for a meeting."""
    id: int
    title: str
    meeting_url: Optional[str]
    platform: str
    status: str
    mode: str
    scheduled_start: Optional[datetime]
    scheduled_end: Optional[datetime]
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    language: str
    participants: Optional[List[str]]
    notes: Optional[dict]
    action_items: Optional[List[dict]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MeetingNotesRequest(BaseModel):
    """Request model for generating meeting notes."""
    transcript: str = Field(..., min_length=10)
    meeting_title: str = Field(..., min_length=1)
    language: str = "en"
    participants: Optional[List[str]] = None


class MeetingNotesResponse(BaseModel):
    """Response model for generated meeting notes."""
    notes: MeetingNotes
    meeting_id: Optional[int] = None
