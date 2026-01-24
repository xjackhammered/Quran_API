"""
Text-to-Speech Feature
======================
Provides Quran audio recitation functionality.
"""

from app.features.tts.service import QuranTTSService, get_quran_tts_service
from app.features.tts.router import router

__all__ = ["QuranTTSService", "get_quran_tts_service", "router"]
