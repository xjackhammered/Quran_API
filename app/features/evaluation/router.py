"""
Recitation Evaluation API Router
================================
FastAPI router for evaluating Quran recitation accuracy.

Endpoints:
    POST /recitation - Evaluate transcribed text against Quran
    POST /audio - Transcribe audio and evaluate (combined)
    GET /reference/{surah}/{ayah} - Get reference text for comparison
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud
from app.features.evaluation.service import (
    RecitationEvaluator,
    get_evaluator,
    EvaluationResult,
    WordFeedback,
    WordStatus
)
from app.features.stt.service import get_stt_service

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class WordFeedbackResponse(BaseModel):
    """Feedback for a single word"""
    reference_word: str
    user_word: str
    status: str
    color: str
    accuracy: float
    note: Optional[str] = None


class EvaluationRequest(BaseModel):
    """Request to evaluate transcribed text"""
    surah_number: int
    ayah_start: int
    ayah_end: Optional[int] = None
    transcribed_text: str


class EvaluationResponse(BaseModel):
    """Evaluation result"""
    surah_number: int
    ayah_range: str
    overall_accuracy: float
    total_words: int
    correct_words: int
    similar_words: int
    wrong_words: int
    missing_words: int
    extra_words: int
    reference_text: str
    user_text: str
    word_feedback: List[WordFeedbackResponse]
    suggestions: List[str]


class AudioEvaluationRequest(BaseModel):
    """Request for combined transcription + evaluation"""
    surah_number: int
    ayah_start: int
    ayah_end: Optional[int] = None
    audio_base64: str
    preprocess: bool = True


class AudioEvaluationResponse(BaseModel):
    """Combined transcription and evaluation result"""
    transcription: dict
    evaluation: EvaluationResponse


class ReferenceTextResponse(BaseModel):
    """Reference text for evaluation"""
    surah_number: int
    surah_name_ar: str
    surah_name_en: str
    ayah_start: int
    ayah_end: int
    text: str
    word_count: int


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _convert_feedback_to_response(feedback: List[WordFeedback]) -> List[WordFeedbackResponse]:
    """Convert internal WordFeedback to API response format"""
    return [
        WordFeedbackResponse(
            reference_word=f.reference_word,
            user_word=f.user_word,
            status=f.status.value,
            color=f.color,
            accuracy=f.accuracy,
            note=f.note
        )
        for f in feedback
    ]


def _get_reference_text(
    db: Session,
    surah_number: int,
    ayah_start: int,
    ayah_end: Optional[int] = None
) -> str:
    """Get reference text from database"""
    if ayah_end is None:
        ayah_end = ayah_start
    
    return crud.get_ayah_text_range(db, surah_number, ayah_start, ayah_end)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/recitation", response_model=EvaluationResponse)
async def evaluate_recitation(
    request: EvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Evaluate a transcribed recitation against the Quran text.
    
    Compare the user's transcribed text against the reference Quran text
    and get word-by-word feedback with color coding.
    
    Args:
        surah_number: Surah number (1-114)
        ayah_start: Starting ayah number
        ayah_end: Ending ayah number (optional, defaults to ayah_start)
        transcribed_text: User's transcribed recitation
    """
    # Validate surah number
    if not 1 <= request.surah_number <= 114:
        raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")
    
    # Get reference text from database
    ayah_end = request.ayah_end or request.ayah_start
    reference_text = _get_reference_text(
        db, request.surah_number, request.ayah_start, ayah_end
    )
    
    if not reference_text:
        raise HTTPException(
            status_code=404,
            detail=f"Ayah not found: Surah {request.surah_number}, Ayah {request.ayah_start}-{ayah_end}"
        )
    
    # Evaluate
    evaluator = get_evaluator()
    result = evaluator.evaluate(reference_text, request.transcribed_text)
    
    # Build response
    return EvaluationResponse(
        surah_number=request.surah_number,
        ayah_range=f"{request.ayah_start}-{ayah_end}" if ayah_end != request.ayah_start else str(request.ayah_start),
        overall_accuracy=result.overall_accuracy,
        total_words=result.total_words,
        correct_words=result.correct_words,
        similar_words=result.similar_words,
        wrong_words=result.wrong_words,
        missing_words=result.missing_words,
        extra_words=result.extra_words,
        reference_text=result.reference_text,
        user_text=result.user_text,
        word_feedback=_convert_feedback_to_response(result.word_feedback),
        suggestions=result.suggestions
    )


@router.post("/audio", response_model=AudioEvaluationResponse)
async def evaluate_audio(
    request: AudioEvaluationRequest,
    db: Session = Depends(get_db)
):
    """
    Transcribe audio and evaluate in one step.
    
    This is the main endpoint for the complete flow:
    1. Receive audio (base64)
    2. Transcribe using Arabic STT
    3. Compare against Quran text
    4. Return detailed feedback
    
    Args:
        surah_number: Surah number (1-114)
        ayah_start: Starting ayah number
        ayah_end: Ending ayah number (optional)
        audio_base64: Base64 encoded audio (WAV format)
        preprocess: Apply audio preprocessing (recommended)
    """
    # Validate
    if not 1 <= request.surah_number <= 114:
        raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")
    
    # Get STT service
    stt_service = get_stt_service()
    if not stt_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Speech-to-Text service unavailable. Configure OPENAI_API_KEY."
        )
    
    # Transcribe audio
    try:
        transcription = await stt_service.transcribe_base64(
            request.audio_base64,
            request.preprocess,
            "ar"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    if not transcription.text:
        raise HTTPException(
            status_code=400,
            detail="No speech detected in audio. Please try again."
        )
    
    # Get reference text
    ayah_end = request.ayah_end or request.ayah_start
    reference_text = _get_reference_text(
        db, request.surah_number, request.ayah_start, ayah_end
    )
    
    if not reference_text:
        raise HTTPException(
            status_code=404,
            detail=f"Ayah not found: Surah {request.surah_number}, Ayah {request.ayah_start}"
        )
    
    # Evaluate
    evaluator = get_evaluator()
    result = evaluator.evaluate(reference_text, transcription.text)
    
    # Build response
    return AudioEvaluationResponse(
        transcription={
            "text": transcription.text,
            "confidence": transcription.confidence,
            "duration": transcription.duration
        },
        evaluation=EvaluationResponse(
            surah_number=request.surah_number,
            ayah_range=f"{request.ayah_start}-{ayah_end}" if ayah_end != request.ayah_start else str(request.ayah_start),
            overall_accuracy=result.overall_accuracy,
            total_words=result.total_words,
            correct_words=result.correct_words,
            similar_words=result.similar_words,
            wrong_words=result.wrong_words,
            missing_words=result.missing_words,
            extra_words=result.extra_words,
            reference_text=result.reference_text,
            user_text=result.user_text,
            word_feedback=_convert_feedback_to_response(result.word_feedback),
            suggestions=result.suggestions
        )
    )


@router.get("/reference/{surah_number}/{ayah_start}", response_model=ReferenceTextResponse)
async def get_reference_text_endpoint(
    surah_number: int,
    ayah_start: int,
    ayah_end: Optional[int] = Query(None, description="End ayah (optional)"),
    db: Session = Depends(get_db)
):
    """
    Get reference Quran text for a specific ayah range.
    
    Use this to display the text the user should recite.
    """
    if not 1 <= surah_number <= 114:
        raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")
    
    # Get surah info
    surah = crud.get_surah_by_number(db, surah_number)
    if not surah:
        raise HTTPException(status_code=404, detail=f"Surah {surah_number} not found")
    
    # Get text
    end = ayah_end or ayah_start
    text = crud.get_ayah_text_range(db, surah_number, ayah_start, end)
    
    if not text:
        raise HTTPException(
            status_code=404,
            detail=f"Ayah not found: Surah {surah_number}, Ayah {ayah_start}"
        )
    
    # Count words
    word_count = len(text.split())
    
    return ReferenceTextResponse(
        surah_number=surah_number,
        surah_name_ar=surah.name_ar,
        surah_name_en=surah.name_en,
        ayah_start=ayah_start,
        ayah_end=end,
        text=text,
        word_count=word_count
    )


@router.post("/compare-text")
async def compare_texts(
    reference_text: str = Query(..., description="Reference Quran text"),
    user_text: str = Query(..., description="User's transcribed text")
):
    """
    Direct text comparison without database lookup.
    
    Useful for testing or when you already have the reference text.
    """
    if not reference_text or not user_text:
        raise HTTPException(status_code=400, detail="Both texts are required")
    
    evaluator = get_evaluator()
    result = evaluator.evaluate(reference_text, user_text)
    
    return {
        "overall_accuracy": result.overall_accuracy,
        "total_words": result.total_words,
        "correct_words": result.correct_words,
        "similar_words": result.similar_words,
        "wrong_words": result.wrong_words,
        "word_feedback": _convert_feedback_to_response(result.word_feedback),
        "suggestions": result.suggestions
    }
