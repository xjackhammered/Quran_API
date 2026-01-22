from fastapi import APIRouter, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from app.audio_utils import transcribe_audio, process_audio_base64
from app.realtime_stt import RealtimeSTT
import numpy as np
import scipy.io.wavfile as wavfile
import io
import asyncio

router = APIRouter(prefix="/stt", tags=["Speech-to-Text"])

# Store active WebSocket sessions
stt_sessions = {}


class AudioBase64Request(BaseModel):
    audio_data: str  # base64 encoded audio
    sample_rate: int = 16000


class TranscriptionResponse(BaseModel):
    success: bool
    text: str
    error: str | None = None


@router.post("/transcribe-file", response_model=TranscriptionResponse)
async def transcribe_file(file: UploadFile = File(...)):
    """
    Transcribe audio from uploaded WAV file
    
    Upload a WAV file and get Arabic transcription
    """
    try:
        # Read file
        contents = await file.read()
        
        # Parse WAV file
        sample_rate, audio_data = wavfile.read(io.BytesIO(contents))
        
        # Convert to float32 if needed
        if audio_data.dtype == np.int16:
            audio_data = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.int32:
            audio_data = audio_data.astype(np.float32) / 2147483648.0
        
        # Handle stereo to mono
        if len(audio_data.shape) > 1:
            audio_data = audio_data.mean(axis=1)
        
        # Transcribe
        result = transcribe_audio(audio_data, sample_rate)
        
        return TranscriptionResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing audio: {str(e)}")


@router.post("/transcribe-base64", response_model=TranscriptionResponse)
async def transcribe_base64(request: AudioBase64Request):
    """
    Transcribe audio from base64 encoded data
    
    Send base64 encoded audio (float32 array) and sample rate
    """
    result = process_audio_base64(request.audio_data, request.sample_rate)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return TranscriptionResponse(**result)


@router.websocket("/ws/realtime")
async def realtime_transcription(websocket: WebSocket):
    """
    Real-time speech-to-text via WebSocket
    
    Connect to this endpoint to start real-time transcription.
    The server will listen to your microphone and send transcriptions back.
    
    Messages from server:
    - {"type": "transcription", "text": "transcribed text"}
    - {"type": "status", "message": "status message"}
    - {"type": "error", "message": "error message"}
    
    Messages to server:
    - "stop" - stop transcription and close connection
    """
    await websocket.accept()
    
    session_id = id(websocket)
    stt = RealtimeSTT()
    stt_sessions[session_id] = stt
    
    async def on_transcription(text: str):
        """Callback when transcription is ready"""
        try:
            await websocket.send_json({
                "type": "transcription",
                "text": text
            })
        except Exception as e:
            print(f"Error sending transcription: {e}")
    
    try:
        # Send initial status
        await websocket.send_json({
            "type": "status",
            "message": "Connected. Starting speech recognition..."
        })
        
        # Start listening
        stt.start(lambda text: asyncio.create_task(on_transcription(text)))
        
        await websocket.send_json({
            "type": "status",
            "message": "Listening... Speak now!"
        })
        
        # Keep connection alive and listen for commands
        while True:
            try:
                data = await websocket.receive_text()
                
                if data == "stop":
                    await websocket.send_json({
                        "type": "status",
                        "message": "Stopping transcription..."
                    })
                    break
                    
            except WebSocketDisconnect:
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
        # Cleanup
        stt.stop()
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


@router.get("/sessions")
async def get_active_sessions():
    """Get number of active real-time transcription sessions"""
    return {
        "active_sessions": len(stt_sessions),
        "session_ids": list(stt_sessions.keys())
    }
