"""
Speech-to-Text API Routes - FIXED VERSION
Uses queue-based async communication to avoid event loop issues
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
import numpy as np
import scipy.io.wavfile as wavfile
import io
import os
import tempfile
import asyncio
import queue
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter(prefix="/stt", tags=["Speech-to-Text"])

# Store active sessions
stt_sessions = {}


class TranscriptionResponse(BaseModel):
    success: bool
    text: str
    error: Optional[str] = None


def transcribe_audio_data(audio_data: np.ndarray, sample_rate: int = 16000) -> dict:
    """Transcribe audio using Whisper API"""
    try:
        # Normalize
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))
        
        # Convert to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        wavfile.write(temp_file.name, sample_rate, audio_int16)
        temp_file.close()
        
        # Transcribe
        with open(temp_file.name, 'rb') as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="ar",
                response_format="text"
            )
        
        # Cleanup
        os.remove(temp_file.name)
        
        return {
            "success": True,
            "text": transcript.strip() if transcript else "",
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": str(e)
        }


@router.post("/transcribe-file", response_model=TranscriptionResponse)
async def transcribe_file(file: UploadFile = File(...)):
    """
    Transcribe audio from uploaded WAV file
    """
    try:
        contents = await file.read()
        sample_rate, audio_data = wavfile.read(io.BytesIO(contents))
        
        # Convert to float32
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            audio_data = audio_data.astype(np.float32) / 2147483648.0
        
        # Stereo to mono
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
        
        result = transcribe_audio_data(audio_data, sample_rate)
        return TranscriptionResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


@router.websocket("/ws/realtime")
async def realtime_transcription(websocket: WebSocket):
    """
    Real-time speech-to-text via WebSocket
    
    Uses a message queue to safely communicate between sync threads and async websocket.
    """
    await websocket.accept()
    
    session_id = id(websocket)
    
    # Import here to avoid circular imports
    from app.realtime_stt import RealtimeSTT
    
    stt = RealtimeSTT()
    stt_sessions[session_id] = stt
    
    # Message queue for thread-safe communication
    message_queue = queue.Queue()
    is_running = True
    
    # Sync callbacks that put messages in queue (thread-safe)
    def on_transcription(text: str):
        message_queue.put({"type": "transcription", "text": text})
    
    def on_status(message: str):
        message_queue.put({"type": "status", "message": message})
    
    try:
        await websocket.send_json({
            "type": "status",
            "message": "Connected. Starting speech recognition..."
        })
        
        # Set callbacks
        stt.status_callback = on_status
        
        # Start listening
        stt.start(on_transcription)
        
        await websocket.send_json({
            "type": "status",
            "message": "Listening... Speak now!"
        })
        
        # Main loop: check for messages and websocket data
        while is_running:
            # Check message queue (non-blocking)
            try:
                while True:
                    msg = message_queue.get_nowait()
                    await websocket.send_json(msg)
            except queue.Empty:
                pass
            
            # Check for websocket messages with timeout
            try:
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=0.1  # 100ms timeout
                )
                
                if data == "stop":
                    await websocket.send_json({
                        "type": "status",
                        "message": "Stopping..."
                    })
                    is_running = False
                    break
                    
            except asyncio.TimeoutError:
                # No message, continue loop
                continue
            except WebSocketDisconnect:
                is_running = False
                break
                
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except:
            pass
    finally:
        is_running = False
        stt.stop()
        
        # Send any remaining messages in queue
        try:
            while True:
                msg = message_queue.get_nowait()
                await websocket.send_json(msg)
        except queue.Empty:
            pass
        except:
            pass
        
        if session_id in stt_sessions:
            del stt_sessions[session_id]
        
        try:
            await websocket.close()
        except:
            pass


@router.get("/health")
async def health_check():
    """Check if STT service is working"""
    return {
        "status": "ok",
        "service": "speech-to-text",
        "active_sessions": len(stt_sessions)
    }
