"""
Quran TTS API Router
====================
FastAPI router for Text-to-Speech (Read Aloud) feature.

Endpoints:
    GET /surahs - List all 114 surahs
    GET /surahs/{number} - Get surah details
    GET /reciters - List all available reciters
    GET /playback/{surah} - Get playback-ready data for frontend
    GET /audio/ayah/{surah}/{ayah} - Get audio for specific ayah
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.features.tts.service import (
    QuranTTSService,
    SurahInfo,
    ReciterInfo,
    AyahAudio,
    SurahAudio,
    PlaybackInfo,
    get_quran_tts_service,
    get_global_ayah_number,
    get_surah_ayah_from_global,
)

router = APIRouter()


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class SurahListResponse(BaseModel):
    total: int
    surahs: List[SurahInfo]


class ReciterListResponse(BaseModel):
    total: int
    reciters: List[ReciterInfo]


class AudioUrlResponse(BaseModel):
    surah_number: int
    ayah_number: int
    text: str
    audio_url: str
    audio_fallbacks: List[str]
    reciter: str


# ============================================================================
# SURAH ENDPOINTS
# ============================================================================

@router.get("/surahs", response_model=SurahListResponse)
async def get_all_surahs():
    """Get list of all 114 Surahs with metadata"""
    service = get_quran_tts_service()
    surahs = service.get_all_surahs()
    return SurahListResponse(total=len(surahs), surahs=surahs)


@router.get("/surahs/{surah_number}", response_model=SurahInfo)
async def get_surah_info(surah_number: int):
    """Get information about a specific Surah"""
    if not 1 <= surah_number <= 114:
        raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")
    
    service = get_quran_tts_service()
    surah = service.get_surah_info(surah_number)
    
    if not surah:
        raise HTTPException(status_code=404, detail=f"Surah {surah_number} not found")
    
    return surah


# ============================================================================
# RECITER ENDPOINTS
# ============================================================================

@router.get("/reciters", response_model=ReciterListResponse)
async def get_all_reciters(
    gender: Optional[str] = Query(None, description="Filter by gender: 'male' or 'female'")
):
    """Get list of all available Quran reciters"""
    if gender and gender not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Gender must be 'male' or 'female'")
    
    service = get_quran_tts_service()
    reciters = service.get_all_reciters(gender=gender)
    return ReciterListResponse(total=len(reciters), reciters=reciters)


@router.get("/reciters/{identifier}", response_model=ReciterInfo)
async def get_reciter_info(identifier: str):
    """Get information about a specific reciter"""
    service = get_quran_tts_service()
    reciter = service.get_reciter_info(identifier)
    
    if not reciter:
        raise HTTPException(status_code=404, detail=f"Reciter '{identifier}' not found")
    
    return reciter


# ============================================================================
# AUDIO ENDPOINTS
# ============================================================================

@router.get("/audio/ayah/{surah_number}/{ayah_number}", response_model=AudioUrlResponse)
async def get_ayah_audio(
    surah_number: int,
    ayah_number: int,
    reciter: str = Query("ar.alafasy", description="Reciter identifier"),
    bitrate: int = Query(128, description="Audio bitrate")
):
    """Get audio URL for a specific Ayah"""
    if not 1 <= surah_number <= 114:
        raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")
    
    service = get_quran_tts_service()
    result = await service.get_ayah_audio(surah_number, ayah_number, reciter, bitrate)
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch audio for Surah {surah_number}, Ayah {ayah_number}"
        )
    
    return AudioUrlResponse(
        surah_number=surah_number,
        ayah_number=ayah_number,
        text=result.text,
        audio_url=result.audio_url,
        audio_fallbacks=result.audio_secondary,
        reciter=reciter
    )


@router.get("/audio/surah/{surah_number}", response_model=SurahAudio)
async def get_surah_audio(
    surah_number: int,
    reciter: str = Query("ar.alafasy", description="Reciter identifier"),
    bitrate: int = Query(128, description="Audio bitrate")
):
    """Get audio URLs for an entire Surah"""
    if not 1 <= surah_number <= 114:
        raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")
    
    service = get_quran_tts_service()
    result = await service.get_surah_audio(surah_number, reciter, bitrate)
    
    if not result:
        raise HTTPException(
            status_code=404, 
            detail=f"Could not fetch audio for Surah {surah_number}"
        )
    
    return result


# ============================================================================
# PLAYBACK ENDPOINT (Main endpoint for frontend)
# ============================================================================

@router.get("/playback/{surah_number}", response_model=PlaybackInfo)
async def get_playback_data(
    surah_number: int,
    reciter: str = Query("ar.alafasy", description="Reciter identifier"),
    bitrate: int = Query(128, description="Audio bitrate"),
    start_ayah: Optional[int] = Query(None, description="Start from this ayah"),
    end_ayah: Optional[int] = Query(None, description="End at this ayah")
):
    """
    Get all data needed to play a Surah in the frontend.
    
    This is the MAIN ENDPOINT for the TTS feature. Returns:
    - Surah info (name in English and Arabic)
    - Reciter name
    - List of all ayahs with text and audio URLs
    """
    if not 1 <= surah_number <= 114:
        raise HTTPException(status_code=400, detail="Surah number must be between 1 and 114")
    
    if bitrate not in [192, 128, 64, 32]:
        raise HTTPException(status_code=400, detail="Bitrate must be 192, 128, 64, or 32")
    
    service = get_quran_tts_service()
    result = await service.get_playback_info(
        surah_number, reciter, bitrate, start_ayah, end_ayah
    )
    
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch playback data for Surah {surah_number}"
        )
    
    return result


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get("/convert/to-global")
async def convert_to_global_ayah(
    surah_number: int = Query(..., description="Surah number (1-114)"),
    ayah_number: int = Query(..., description="Ayah number within the Surah")
):
    """Convert Surah:Ayah reference to global ayah number (1-6236)"""
    try:
        global_number = get_global_ayah_number(surah_number, ayah_number)
        return {
            "surah_number": surah_number,
            "ayah_number": ayah_number,
            "global_ayah_number": global_number
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/convert/from-global")
async def convert_from_global_ayah(
    global_number: int = Query(..., description="Global ayah number (1-6236)")
):
    """Convert global ayah number to Surah:Ayah reference"""
    try:
        surah_number, ayah_number = get_surah_ayah_from_global(global_number)
        service = get_quran_tts_service()
        surah_info = service.get_surah_info(surah_number)
        
        return {
            "global_ayah_number": global_number,
            "surah_number": surah_number,
            "surah_name": surah_info.englishName if surah_info else None,
            "ayah_number": ayah_number
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
