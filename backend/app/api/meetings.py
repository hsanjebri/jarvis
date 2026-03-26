"""
Meeting API Routes

Endpoints for meeting management and note generation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.meeting import Meeting, MeetingStatus
from app.schemas.meeting import (
    MeetingCreate,
    MeetingUpdate,
    MeetingResponse,
    MeetingNotesRequest,
    MeetingNotesResponse,
)
from app.ai.claude_client import claude_client
from app.ai.whisper_client import whisper_client

router = APIRouter()


@router.get("/", response_model=List[MeetingResponse])
async def list_meetings(
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """List all meetings with optional status filter."""
    query = select(Meeting).order_by(Meeting.created_at.desc())
    
    if status:
        query = query.where(Meeting.status == status)
    
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    meetings = result.scalars().all()
    
    return meetings


@router.post("/", response_model=MeetingResponse)
async def create_meeting(
    meeting: MeetingCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new meeting."""
    try:
        # Convert string mode to Enum
        from app.models.meeting import MeetingMode
        
        # Parse start/end times if they are strings (though Pydantic should handle this)
        # mode is likely the issue if passed as string to SQLAlchemy Enum
        mode_enum = MeetingMode(meeting.mode) if isinstance(meeting.mode, str) else meeting.mode
        
        db_meeting = Meeting(
            title=meeting.title,
            meeting_url=meeting.meeting_url,
            platform=meeting.platform,
            scheduled_start=meeting.scheduled_start,
            scheduled_end=meeting.scheduled_end,
            mode=mode_enum,
            language=meeting.language,
            status=MeetingStatus.SCHEDULED,
        )
        
        db.add(db_meeting)
        await db.commit()
        await db.refresh(db_meeting)
        
        return db_meeting
    except Exception as e:
        print(f"❌ Error creating meeting: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get a meeting by ID."""
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    return meeting


@router.patch("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: int,
    meeting_update: MeetingUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a meeting."""
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    update_data = meeting_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meeting, field, value)
    
    await db.commit()
    await db.refresh(meeting)
    
    return meeting


@router.delete("/{meeting_id}")
async def delete_meeting(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete a meeting."""
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    await db.delete(meeting)
    await db.commit()
    
    return {"status": "deleted", "meeting_id": meeting_id}


@router.post("/generate-notes", response_model=MeetingNotesResponse)
async def generate_notes(request: MeetingNotesRequest):
    """Generate meeting notes from a transcript using Claude."""
    notes = await claude_client.generate_meeting_notes(
        transcript=request.transcript,
        meeting_title=request.meeting_title,
        language=request.language,
        participants=request.participants,
    )
    
    return MeetingNotesResponse(notes=notes)


@router.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = None,
):
    """Transcribe an audio file using Whisper."""
    # Read the uploaded file
    audio_bytes = await audio.read()
    
    # Create a file-like object
    import io
    audio_file = io.BytesIO(audio_bytes)
    
    # Transcribe
    result = await whisper_client.transcribe_audio(
        audio_file=audio_file,
        filename=audio.filename or "audio.webm",
        language=language,
    )
    
    return result


@router.post("/{meeting_id}/transcribe-and-generate")
async def transcribe_and_generate_notes(
    meeting_id: int,
    audio: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Full workflow: Upload audio, transcribe, generate notes, and update meeting.
    
    This is the main endpoint for processing a recorded meeting.
    """
    # Get the meeting
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Read and transcribe the audio
    audio_bytes = await audio.read()
    import io
    audio_file = io.BytesIO(audio_bytes)
    
    transcript_result = await whisper_client.transcribe_audio(
        audio_file=audio_file,
        filename=audio.filename or "audio.webm",
        language=meeting.language,
    )
    
    # Generate notes from transcript
    notes = await claude_client.generate_meeting_notes(
        transcript=transcript_result["text"],
        meeting_title=meeting.title,
        language=transcript_result.get("language", meeting.language),
        participants=meeting.participants,
    )
    
    # Update the meeting
    meeting.raw_transcript = transcript_result["text"]
    meeting.notes = notes
    meeting.action_items = notes.get("action_items", [])
    meeting.status = MeetingStatus.COMPLETED
    
    await db.commit()
    await db.refresh(meeting)
    
    return {
        "meeting_id": meeting.id,
        "transcript": transcript_result,
        "notes": notes,
        "status": "completed"
    }


@router.post("/{meeting_id}/join")
async def join_meeting_browser(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Join a meeting using browser automation.
    
    This will launch a browser and attempt to join the meeting via Google Meet.
    The agent will mute mic/camera by default (SILENT mode).
    """
    from app.agents.meeting_agent import meeting_agent, AgentMode
    
    # Get the meeting
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    if not meeting.meeting_url:
        raise HTTPException(status_code=400, detail="Meeting URL is required")
    
    # Parse mode from meeting
    mode_map = {
        "silent": AgentMode.SILENT,
        "represent": AgentMode.REPRESENT,
        "assist": AgentMode.ASSIST,
    }
    mode = mode_map.get(meeting.mode.value if hasattr(meeting.mode, 'value') else meeting.mode, AgentMode.SILENT)
    
    # Join the meeting
    session = await meeting_agent.join_meeting(
        meeting_id=meeting_id,
        meeting_url=meeting.meeting_url,
        mode=mode,
    )
    
    # Update meeting status
    meeting.status = MeetingStatus.IN_PROGRESS
    await db.commit()
    
    return {
        "meeting_id": meeting_id,
        "browser_state": session.browser_state,
        "is_active": session.is_active,
        "started_at": session.started_at.isoformat() if session.started_at else None,
    }


@router.post("/{meeting_id}/leave")
async def leave_meeting_browser(
    meeting_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Leave the current meeting.
    
    This will close the browser and end the meeting session.
    """
    from app.agents.meeting_agent import meeting_agent
    
    # Get the meeting
    result = await db.execute(
        select(Meeting).where(Meeting.id == meeting_id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found")
    
    # Leave the meeting
    success = await meeting_agent.leave_meeting(meeting_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Not currently in this meeting")
    
    return {
        "meeting_id": meeting_id,
        "status": "left",
    }


@router.get("/agent/status")
async def get_agent_status():
    """
    Get the current status of the meeting agent.
    
    Returns information about active meeting sessions.
    """
    from app.agents.meeting_agent import meeting_agent
    
    sessions = meeting_agent.get_active_sessions()
    
    return {
        "active_sessions": [
            {
                "meeting_id": s.meeting_id,
                "meeting_url": s.meeting_url,
                "mode": s.mode.value,
                "browser_state": s.browser_state,
                "is_active": s.is_active,
                "started_at": s.started_at.isoformat() if s.started_at else None,
            }
            for s in sessions
        ],
        "total_active": len(sessions),
    }

