"""
Speech-to-Text API Router
=========================
FastAPI router for Arabic speech recognition.

Endpoints:
    POST /transcribe - Transcribe audio from base64
    POST /transcribe-file - Transcribe uploaded audio file
    GET /health - Check STT service status
    GET /stats - Get transcription statistics
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel
from typing import Optional
import tempfile
import os

from app.features.stt.service import get_stt_service, TranscriptionResult

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class TranscribeRequest(BaseModel):
    """Request for audio transcription"""
    audio_base64: str
    preprocess: bool = True
    language: str = "ar"


class TranscribeResponse(BaseModel):
    """Transcription result"""
    text: str
    confidence: str
    duration: Optional[float] = None
    language: str = "ar"


class STTHealthResponse(BaseModel):
    """STT service health status"""
    status: str
    api_available: bool
    message: str


class STTStatsResponse(BaseModel):
    """Transcription statistics"""
    total_transcriptions: int
    successful_transcriptions: int
    success_rate: float


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(request: TranscribeRequest):
    """
    Transcribe Arabic audio from base64.
    
    Send audio as base64-encoded WAV or raw PCM.
    Returns transcribed Arabic text.
    
    Args:
        audio_base64: Base64 encoded audio
        preprocess: Apply audio preprocessing (recommended)
        language: Target language (default: ar for Arabic)
    """
    service = get_stt_service()
    
    if not service.is_available():
        raise HTTPException(
            status_code=503,
            detail="STT service unavailable. OpenAI API key not configured."
        )
    
    try:
        result = await service.transcribe_base64(
            request.audio_base64,
            request.preprocess,
            request.language
        )
        
        return TranscribeResponse(
            text=result.text,
            confidence=result.confidence,
            duration=result.duration,
            language=result.language
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


@router.post("/transcribe-file", response_model=TranscribeResponse)
async def transcribe_file(
    file: UploadFile = File(...),
    preprocess: bool = Query(True, description="Apply audio preprocessing"),
    language: str = Query("ar", description="Target language")
):
    """
    Transcribe uploaded audio file.
    
    Accepts WAV files. Returns transcribed Arabic text.
    """
    service = get_stt_service()
    
    if not service.is_available():
        raise HTTPException(
            status_code=503,
            detail="STT service unavailable. OpenAI API key not configured."
        )
    
    # Validate file type
    if not file.filename.endswith(('.wav', '.WAV')):
        raise HTTPException(
            status_code=400,
            detail="Only WAV files are supported"
        )
    
    # Save uploaded file temporarily
    fd, temp_path = tempfile.mkstemp(suffix='.wav')
    try:
        os.close(fd)
        
        # Write uploaded content
        content = await file.read()
        with open(temp_path, 'wb') as f:
            f.write(content)
        
        # Transcribe
        result = await service.transcribe_file(temp_path, preprocess, language)
        
        return TranscribeResponse(
            text=result.text,
            confidence=result.confidence,
            duration=result.duration,
            language=result.language
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    finally:
        # Cleanup
        try:
            os.remove(temp_path)
        except:
            pass


@router.get("/health", response_model=STTHealthResponse)
async def check_health():
    """Check STT service health and API availability"""
    service = get_stt_service()
    is_available = service.is_available()
    
    return STTHealthResponse(
        status="healthy" if is_available else "degraded",
        api_available=is_available,
        message="STT service ready" if is_available else "OpenAI API key not configured"
    )


@router.get("/stats", response_model=STTStatsResponse)
async def get_stats():
    """Get transcription statistics"""
    service = get_stt_service()
    stats = service.get_stats()
    
    return STTStatsResponse(**stats)
