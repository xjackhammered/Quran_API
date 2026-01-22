"""
Quran API with Speech-to-Text
============================

A FastAPI application providing:
- Quran Surah and Ayah API
- Advanced Arabic Speech-to-Text (optimized for Quranic recitation)
- Real-time WebSocket transcription
- Web-based GUI interfaces

Modules:
- main: FastAPI application entry point
- database: SQLAlchemy database configuration
- models: Database models (Surah, Ayah)
- schemas: Pydantic validation schemas
- crud: Database CRUD operations
- audio_utils: Advanced audio processing and transcription
- realtime_stt: Real-time speech-to-text engine
- stt_routes: Speech-to-text API routes
- stt_gui: Web GUI interfaces
"""

__version__ = "2.0.0"
__author__ = "Emon"
