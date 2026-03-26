"""
Streaming API Routes

WebSocket endpoints for real-time audio streaming and transcription.
"""

import asyncio
import json
import io
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ai.gemini_client import gemini_client

router = APIRouter()

@router.websocket("/ws/audio/{meeting_id}")
async def websocket_audio_endpoint(websocket: WebSocket, meeting_id: int):
    await websocket.accept()
    print(f"WebSocket connected for meeting {meeting_id}")
    
    # Send immediate confirmation
    await websocket.send_json({
        "type": "transcript",
        "text": "Interview Mode Active (Listening...)",
        "is_final": True
    })
    
    # Audio buffer for this session
    audio_buffer = bytearray()
    chunk_count = 0
    
    try:
        while True:
            # Receive audio chunk as bytes
            data = await websocket.receive_bytes()
            audio_buffer.extend(data)
            chunk_count += 1
            print(f"[WS] Received chunk {chunk_count}, total size: {len(audio_buffer)} bytes")
            
            # Process every 3 chunks (approx 3 seconds of audio with 1s chunks)
            if chunk_count % 3 == 0:
                print(f"Processing audio buffer size with GEMINI: {len(audio_buffer)} bytes...")
                
                try:
                    # Send raw audio bytes to Gemini
                    result = await gemini_client.analyze_audio(bytes(audio_buffer))
                    
                    transcript = result.get("transcript", "")
                    suggestion = result.get("suggestion", "")

                    if transcript and transcript != "Error":
                        print(f"Transcript (Gemini): {transcript}")
                        await websocket.send_json({
                            "type": "transcript",
                            "text": f"Interviewer: {transcript}",
                            "is_final": True
                        })
                    
                    if suggestion and suggestion != "Error":
                        print(f"Suggestion (Gemini): {suggestion}")
                        await websocket.send_json({
                            "type": "transcript",
                            "text": f"JARVIS: {suggestion}",
                            "is_final": True
                        })
                        
                    # Clear buffer after processing
                    audio_buffer = bytearray()
                    
                except Exception as e:
                    print(f"Gemini Processing Error: {e}")
                    # Clear buffer if it gets too huge to avoid crashes
                    if len(audio_buffer) > 3 * 1024 * 1024:
                         audio_buffer = bytearray()

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for meeting {meeting_id}")
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close()
