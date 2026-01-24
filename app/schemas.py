"""
Pydantic Schemas
================
Request/Response models for API validation.
"""

from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


# ============================================================================
# QURAN DATABASE SCHEMAS
# ============================================================================

class AyahOut(BaseModel):
    """Ayah output schema"""
    id: int
    number: int
    text: str

    class Config:
        from_attributes = True


class SurahOut(BaseModel):
    """Surah output schema (list view)"""
    id: int
    number: int
    name_ar: str
    name_en: str
    ayah_count: int

    class Config:
        from_attributes = True


class SurahDetailOut(SurahOut):
    """Surah with all Ayahs"""
    ayahs: List[AyahOut]


# ============================================================================
# EVALUATION SCHEMAS
# ============================================================================

class WordStatus(str, Enum):
    """Status for each word in evaluation"""
    CORRECT = "correct"
    SIMILAR = "similar"
    WRONG = "wrong"
    MISSING = "missing"
    EXTRA = "extra"


class WordFeedback(BaseModel):
    """Feedback for a single word"""
    reference_word: str
    user_word: str
    status: WordStatus
    color: str  # green, yellow, red, orange
    accuracy: float  # 0-100
    note: Optional[str] = None


class EvaluationRequest(BaseModel):
    """Request to evaluate a recitation"""
    surah_number: int
    ayah_start: int
    ayah_end: Optional[int] = None
    transcribed_text: str


class EvaluationResponse(BaseModel):
    """Full evaluation response"""
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
    word_feedback: List[WordFeedback]
    suggestions: List[str]


# ============================================================================
# STT SCHEMAS
# ============================================================================

class TranscriptionRequest(BaseModel):
    """Request for audio transcription"""
    audio_base64: Optional[str] = None
    language: str = "ar"


class TranscriptionResponse(BaseModel):
    """Transcription result"""
    text: str
    confidence: str
    duration: Optional[float] = None


# ============================================================================
# COMBINED EVALUATION + TRANSCRIPTION
# ============================================================================

class ReciteAndEvaluateRequest(BaseModel):
    """Request for combined STT + Evaluation"""
    surah_number: int
    ayah_start: int
    ayah_end: Optional[int] = None
    audio_base64: str  # Base64 encoded audio


class ReciteAndEvaluateResponse(BaseModel):
    """Combined response"""
    transcription: TranscriptionResponse
    evaluation: EvaluationResponse


# ============================================================================
# RECITATION HISTORY
# ============================================================================

class RecitationHistoryOut(BaseModel):
    """Recitation history record"""
    id: int
    surah_id: int
    ayah_start: int
    ayah_end: int
    accuracy_score: int
    transcribed_text: Optional[str]
    timestamp: str

    class Config:
        from_attributes = True
