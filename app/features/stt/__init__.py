"""
Speech-to-Text Feature
======================
Provides Arabic speech recognition optimized for Quranic recitation.
"""

from app.features.stt.service import ArabicSTTService, get_stt_service
from app.features.stt.router import router

__all__ = ["ArabicSTTService", "get_stt_service", "router"]
