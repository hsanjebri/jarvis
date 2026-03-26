"""
Whisper API Client

Wrapper for OpenAI Whisper API for audio transcription.
"""

import io
from typing import Optional, BinaryIO
from openai import OpenAI

from app.config import settings


class WhisperClient:
    """Client for OpenAI Whisper transcription API."""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.whisper_model
    
    async def transcribe_audio(
        self,
        audio_file: BinaryIO,
        filename: str = "audio.webm",
        language: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> dict:
        """
        Transcribe audio to text.
        
        Args:
            audio_file: Audio file bytes/stream
            filename: Name of the audio file (for format detection)
            language: Optional language code (en, fr, ar, etc.)
            prompt: Optional prompt to guide transcription
        
        Returns:
            Transcription result with text and detected language
        """
        # Prepare transcription parameters
        params = {
            "model": self.model,
            "file": (filename, audio_file),
            "response_format": "verbose_json"
        }
        
        if language:
            params["language"] = language
        
        if prompt:
            params["prompt"] = prompt
        
        # Call Whisper API
        transcript = self.client.audio.transcriptions.create(**params)
        
        return {
            "text": transcript.text,
            "language": getattr(transcript, "language", language or "unknown"),
            "duration": getattr(transcript, "duration", None),
            "segments": getattr(transcript, "segments", [])
        }
    
    async def transcribe_with_timestamps(
        self,
        audio_file: BinaryIO,
        filename: str = "audio.webm",
        language: Optional[str] = None
    ) -> list:
        """
        Transcribe audio with word-level timestamps.
        
        Returns:
            List of segments with timestamps
        """
        params = {
            "model": self.model,
            "file": (filename, audio_file),
            "response_format": "verbose_json",
            "timestamp_granularities": ["segment"]
        }
        
        if language:
            params["language"] = language
        
        transcript = self.client.audio.transcriptions.create(**params)
        
        segments = []
        for segment in getattr(transcript, "segments", []):
            segments.append({
                "start": segment.get("start", 0),
                "end": segment.get("end", 0),
                "text": segment.get("text", ""),
            })
        
        return segments
    
    async def detect_language(self, audio_file: BinaryIO, filename: str = "audio.webm") -> str:
        """
        Detect the language of an audio file.
        
        Returns:
            ISO language code (e.g., 'en', 'fr', 'ar')
        """
        transcript = self.client.audio.transcriptions.create(
            model=self.model,
            file=(filename, audio_file),
            response_format="verbose_json"
        )
        
        return getattr(transcript, "language", "unknown")


# Singleton instance
whisper_client = WhisperClient()
