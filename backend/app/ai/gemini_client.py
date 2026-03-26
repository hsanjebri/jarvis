"""
Gemini API Client

Wrapper for Google Generative AI (Gemini 1.5 Flash) for direct audio analysis.
"""

import google.generativeai as genai
from typing import Optional
import io
import os
from app.config import settings

class GeminiClient:
    """Client for Google Gemini 1.5 Flash API."""
    
    def __init__(self):
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
        # We will try these models in order until one works
        self.candidate_models = [
            'gemini-1.5-flash',
            'gemini-flash-latest',
            'gemini-1.5-flash-8b',
            'gemini-2.0-flash-lite',
            'gemini-pro'
        ]
        self.current_model_idx = 0
        self.model = genai.GenerativeModel(self.candidate_models[self.current_model_idx])
    
    async def analyze_audio(self, audio_data: bytes) -> dict:
        """
        Send audio bytes directly to Gemini for transcription and analysis.
        """
        if not settings.gemini_api_key or "your_gemini" in settings.gemini_api_key:
            return {"transcript": "GEMINI_KEY_MISSING", "suggestion": "Please add your GEMINI_API_KEY to the .env file."}

        for _ in range(len(self.candidate_models)):
            try:
                model_name = self.candidate_models[self.current_model_idx]
                print(f"[GEMINI] Trying model: {model_name} with {len(audio_data)} bytes...")
                
                # Update the model instance to the current candidate
                self.model = genai.GenerativeModel(model_name)
                
                prompt = """
                Analyze this audio from a live interview. 
                1. Transcribe exactly what the interviewer just said.
                2. Provide a short, secret response tip (1 sentence) for the candidate.
                
                Return ONLY JSON: {"transcript": "...", "suggestion": "..."}
                """
                
                response = self.model.generate_content([
                    prompt,
                    {
                        "mime_type": "audio/webm",
                        "data": audio_data
                    }
                ])
                
                print(f"[GEMINI] Success with {model_name}!")
                
                # Robust parsing
                text = response.text.replace("```json", "").replace("```", "").strip()
                try:
                    import json
                    return json.loads(text)
                except:
                    return {"transcript": text[:100], "suggestion": "Answer is coming..."}
                
            except Exception as e:
                err_msg = str(e)
                print(f"[GEMINI] Attempt with {self.candidate_models[self.current_model_idx]} failed: {err_msg}")
                
                # If it's a 404 or 429, try the next model
                if "404" in err_msg or "429" in err_msg or "not found" in err_msg.lower():
                    self.current_model_idx = (self.current_model_idx + 1) % len(self.candidate_models)
                    continue
                else:
                    return {"transcript": "Error", "suggestion": err_msg}
        
        return {"transcript": "All models failed", "suggestion": "Check API Key or Region."}

# Singleton instance
gemini_client = GeminiClient()
