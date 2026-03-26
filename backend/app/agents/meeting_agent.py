"""
Meeting Agent

Autonomous agent for joining meetings, recording, transcribing, and generating notes.
"""

from enum import Enum
from typing import Optional, AsyncIterator
from dataclasses import dataclass
from datetime import datetime

from app.ai.claude_client import claude_client
from app.ai.whisper_client import whisper_client
from app.browser.google_meet import google_meet, MeetingState


class AgentMode(str, Enum):
    """Meeting agent operation modes."""
    SILENT = "silent"        # Just record and take notes
    REPRESENT = "represent"  # Can speak on behalf of user
    ASSIST = "assist"        # Sends suggestions via Telegram


@dataclass
class MeetingSession:
    """Represents an active meeting session."""
    meeting_id: int
    meeting_url: str
    mode: AgentMode
    started_at: datetime
    is_active: bool = True
    browser_state: str = "idle"
    transcript_buffer: list = None
    
    def __post_init__(self):
        if self.transcript_buffer is None:
            self.transcript_buffer = []


@dataclass
class MeetingNotes:
    """Generated meeting notes."""
    summary: str
    key_points: list
    decisions: list
    action_items: list
    questions: list
    next_steps: str


class MeetingAgent:
    """
    Autonomous meeting agent.
    
    Capabilities:
    - Join virtual meetings (Google Meet, Zoom, Teams)
    - Record audio in real-time
    - Transcribe using Whisper
    - Generate notes using Claude
    - Send notifications via Telegram
    """
    
    def __init__(self):
        self.active_sessions: dict[int, MeetingSession] = {}
        self.claude = claude_client
        self.whisper = whisper_client
        self.google_meet = google_meet
    
    async def join_meeting(
        self,
        meeting_id: int,
        meeting_url: str,
        mode: AgentMode = AgentMode.SILENT
    ) -> MeetingSession:
        """
        Join a virtual meeting using browser automation.
        
        Args:
            meeting_id: Database ID of the meeting
            meeting_url: URL of the meeting to join
            mode: Operating mode (silent/represent/assist)
        
        Returns:
            MeetingSession object representing the active session
        """
        session = MeetingSession(
            meeting_id=meeting_id,
            meeting_url=meeting_url,
            mode=mode,
            started_at=datetime.now(),
            browser_state="joining",
        )
        
        self.active_sessions[meeting_id] = session
        
        print(f"🎤 Meeting Agent joining: {meeting_url}")
        print(f"   Mode: {mode.value}")
        
        # Use browser automation to join the meeting
        # Only enable mic/camera if in REPRESENT mode
        enable_mic = mode == AgentMode.REPRESENT
        enable_camera = False  # JARVIS doesn't need camera
        
        browser_session = await self.google_meet.join_meeting(
            meeting_url=meeting_url,
            mic_enabled=enable_mic,
            camera_enabled=enable_camera,
        )
        
        # Update session with browser state
        session.browser_state = browser_session.state.value
        session.is_active = browser_session.state in [
            MeetingState.IN_MEETING,
            MeetingState.IN_LOBBY
        ]
        
        if browser_session.state == MeetingState.ERROR:
            print(f"❌ Failed to join: {browser_session.error_message}")
            session.is_active = False
        
        return session
    
    async def leave_meeting(self, meeting_id: int) -> bool:
        """Leave a meeting and stop recording."""
        if meeting_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[meeting_id]
        session.is_active = False
        session.browser_state = "leaving"
        
        # Use browser automation to leave
        success = await self.google_meet.leave_meeting()
        
        if success:
            session.browser_state = "left"
            del self.active_sessions[meeting_id]
            print(f"👋 Meeting Agent left meeting {meeting_id}")
        
        return success
    
    async def transcribe_realtime(
        self,
        audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[dict]:
        """
        Transcribe audio in real-time.
        
        This is a placeholder for streaming transcription.
        
        Args:
            audio_stream: Async iterator of audio chunks
        
        Yields:
            Transcript segments with timestamps
        """
        # TODO: Implement real-time streaming transcription
        # - Buffer audio chunks
        # - Send to Whisper API periodically
        # - Yield transcript segments
        
        async for chunk in audio_stream:
            # Placeholder - would process audio here
            yield {
                "timestamp": datetime.now().isoformat(),
                "text": "[Transcription would appear here]",
                "speaker": "Unknown"
            }
    
    async def generate_notes(
        self,
        transcript: str,
        meeting_title: str,
        language: str = "en",
        participants: Optional[list] = None
    ) -> MeetingNotes:
        """
        Generate structured meeting notes from transcript.
        
        Args:
            transcript: Full meeting transcript
            meeting_title: Title of the meeting
            language: Language of the transcript
            participants: List of participant names
        
        Returns:
            Structured MeetingNotes object
        """
        notes_dict = await self.claude.generate_meeting_notes(
            transcript=transcript,
            meeting_title=meeting_title,
            language=language,
            participants=participants,
        )
        
        return MeetingNotes(
            summary=notes_dict.get("summary", ""),
            key_points=notes_dict.get("key_points", []),
            decisions=notes_dict.get("decisions", []),
            action_items=notes_dict.get("action_items", []),
            questions=notes_dict.get("questions", []),
            next_steps=notes_dict.get("next_steps", ""),
        )
    
    async def send_notification(
        self,
        meeting_id: int,
        message: str,
        requires_approval: bool = False
    ) -> bool:
        """
        Send a notification about the meeting.
        
        This will be connected to the Telegram bot.
        
        Args:
            meeting_id: ID of the meeting
            message: Notification message
            requires_approval: Whether user approval is needed
        
        Returns:
            True if notification was sent successfully
        """
        # TODO: Implement Telegram notification
        # - Format message nicely
        # - Add approval buttons if needed
        # - Send via Telegram Bot API
        
        print(f"📧 Notification for meeting {meeting_id}:")
        print(f"   {message}")
        if requires_approval:
            print("   [Waiting for approval]")
        
        return True
    
    def get_active_sessions(self) -> list[MeetingSession]:
        """Get all active meeting sessions."""
        return list(self.active_sessions.values())
    
    def is_in_meeting(self, meeting_id: int) -> bool:
        """Check if agent is currently in a specific meeting."""
        return meeting_id in self.active_sessions


# Singleton instance
meeting_agent = MeetingAgent()
