"""
Claude API Client

Wrapper for Anthropic Claude API for text generation and analysis.
"""

import json
from typing import Optional
import anthropic

from app.config import settings


class ClaudeClient:
    """Client for interacting with Anthropic's Claude API."""
    
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.claude_api_key)
        self.model = settings.claude_model
        self.max_tokens = settings.claude_max_tokens
    
    async def generate_meeting_notes(
        self,
        transcript: str,
        meeting_title: str,
        language: str = "en",
        participants: Optional[list] = None
    ) -> dict:
        """
        Generate structured meeting notes from a transcript.
        
        Args:
            transcript: The meeting transcript text
            meeting_title: Title of the meeting
            language: Language of the transcript (en/fr/ar)
            participants: List of participant names
        
        Returns:
            Structured notes with summary, key points, decisions, and action items
        """
        participants_str = ", ".join(participants) if participants else "Unknown"
        
        prompt = f"""You are a professional meeting note-taker. Analyze this meeting transcript and generate structured notes.

Meeting Information:
- Title: {meeting_title}
- Language: {language}
- Participants: {participants_str}

Transcript:
{transcript}

Generate comprehensive meeting notes in the following JSON format. Respond ONLY with valid JSON, no markdown:

{{
  "summary": "3-4 sentence executive summary",
  "key_points": [
    "Main point 1",
    "Main point 2"
  ],
  "decisions": [
    {{
      "decision": "What was decided",
      "rationale": "Why this was decided",
      "impact": "Who/what is affected"
    }}
  ],
  "action_items": [
    {{
      "task": "What needs to be done",
      "assigned_to": "Person responsible (or 'Unassigned')",
      "deadline": "When it's due (or 'Not specified')",
      "priority": "high/medium/low"
    }}
  ],
  "questions": [
    "Unresolved question 1"
  ],
  "next_steps": "What happens next"
}}

Important:
- Be concise but comprehensive
- Extract ALL action items with clear ownership
- Note if deadline is unclear
- Respond in the same language as the transcript ({language})"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse the response
        response_text = message.content[0].text
        
        try:
            notes = json.loads(response_text)
        except json.JSONDecodeError:
            # If JSON parsing fails, return a basic structure
            notes = {
                "summary": response_text,
                "key_points": [],
                "decisions": [],
                "action_items": [],
                "questions": [],
                "next_steps": "Review the transcript manually"
            }
        
        return notes
    
    async def draft_response(
        self,
        message_content: str,
        sender: str,
        platform: str,
        context: Optional[str] = None,
        style: Optional[dict] = None,
        language: str = "en"
    ) -> dict:
        """
        Draft a response to a message in the user's style.
        
        Args:
            message_content: The message to respond to
            sender: Who sent the message
            platform: Platform (slack/email/whatsapp)
            context: Additional context (thread history, etc.)
            style: User's communication style preferences
            language: Language to respond in
        
        Returns:
            Draft response with confidence score
        """
        style_instructions = ""
        if style:
            style_instructions = f"""
User's Communication Style:
- Tone: {style.get('tone', 'professional')}
- Emoji frequency: {style.get('emoji_frequency', 'occasional')}
- Average message length: {style.get('avg_message_length', 50)} words
- Common phrases: {', '.join(style.get('common_phrases', []))}
"""
        
        context_str = f"\nContext:\n{context}" if context else ""
        
        prompt = f"""You are an AI assistant drafting a response on behalf of the user.

Message from {sender} on {platform}:
"{message_content}"
{context_str}
{style_instructions}

Instructions:
1. Draft a response that sounds natural and human
2. Match the appropriate tone for {platform}
3. Be helpful and relevant
4. Keep it concise
5. Respond in {language}

Respond with JSON only:
{{
  "draft_text": "The actual message to send",
  "confidence": "high/medium/low",
  "reasoning": "Brief explanation of why you drafted this response"
}}"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        response_text = message.content[0].text
        
        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            result = {
                "draft_text": response_text,
                "confidence": "low",
                "reasoning": "Failed to parse structured response"
            }
        
        return result
    
    async def analyze_urgency(self, message_content: str) -> str:
        """
        Analyze the urgency of a message.
        
        Returns: "low", "medium", or "high"
        """
        prompt = f"""Analyze the urgency of this message. Respond with only one word: low, medium, or high.

Message:
"{message_content}"

Consider:
- Explicit urgency words (ASAP, urgent, deadline)
- Time sensitivity
- Importance of the request

Response (one word only):"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=10,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        urgency = message.content[0].text.strip().lower()
        if urgency not in ["low", "medium", "high"]:
            urgency = "medium"
        
        return urgency


# Singleton instance
claude_client = ClaudeClient()
