"""
Pydantic Schemas
Request/Response models for API validation
"""

from pydantic import BaseModel, Field
from typing import List, Optional


# ============================================================================
# QURAN SCHEMAS
# ============================================================================

class AyahBase(BaseModel):
    """Base Ayah schema"""
    number: int = Field(..., description="Verse number within the Surah")
    text: str = Field(..., description="Arabic text of the verse")


class AyahOut(AyahBase):
    """Ayah output schema"""
    id: int

    class Config:
        from_attributes = True


class SurahBase(BaseModel):
    """Base Surah schema"""
    number: int = Field(..., description="Surah number (1-114)")
    name_ar: str = Field(..., description="Arabic name of the Surah")
    name_en: str = Field(..., description="English name of the Surah")
    ayah_count: int = Field(..., description="Total number of verses")


class SurahOut(SurahBase):
    """Surah output schema (without Ayahs)"""
    id: int

    class Config:
        from_attributes = True


class SurahDetailOut(SurahOut):
    """Surah detail schema (with Ayahs)"""
    ayahs: List[AyahOut] = Field(default=[], description="List of verses")


# ============================================================================
# STT SCHEMAS (Additional)
# ============================================================================

class TranscriptionResult(BaseModel):
    """Transcription result schema"""
    success: bool
    text: str
    error: Optional[str] = None
    confidence: Optional[str] = None
    duration: Optional[float] = None
    language: Optional[str] = None


class AudioAnalysis(BaseModel):
    """Audio analysis schema"""
    duration: float
    sample_rate: int
    samples: int
    energy: float
    zcr: float
    max_amplitude: float
    mean_amplitude: float


class STTConfig(BaseModel):
    """STT configuration schema"""
    sample_rate: int = 16000
    channels: int = 1
    energy_threshold: float = 0.03
    silence_duration: float = 5.0
    min_speech_duration: float = 1.0
    max_speech_duration: float = 30.0
    preprocess_mode: str = "standard"


class SessionStatistics(BaseModel):
    """Session statistics schema"""
    total_transcriptions: int = 0
    successful_transcriptions: int = 0
    failed_transcriptions: int = 0
    success_rate: float = 0.0
    total_audio_duration: float = 0.0
    session_duration: float = 0.0
