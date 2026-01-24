"""
Quran Recitation Evaluation App - Main Application
===================================================
Integrated FastAPI backend combining:
1. Quran Database API (Surahs & Ayahs)
2. Text-to-Speech (Read Aloud) Feature
3. Speech-to-Text (Arabic Whisper) Feature
4. Recitation Evaluation (Accuracy Matching)

Run with: uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from pathlib import Path
import os

# Database imports
from app.database import get_db, engine, Base

# Feature routers
from app.features.tts.router import router as tts_router
from app.features.stt.router import router as stt_router
from app.features.evaluation.router import router as evaluation_router

# Core Quran API
from app import crud, schemas


# ============================================================================
# LIFESPAN MANAGER (Startup/Shutdown)
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    # Startup
    print("=" * 60)
    print("🕌 Quran Recitation Evaluation App Starting...")
    print("=" * 60)
    print("\n📚 Available Features:")
    print("   • Quran Database API: /surahs, /surahs/{id}, /ayahs/{surah}/{ayah}")
    print("   • Text-to-Speech:     /api/tts/...")
    print("   • Speech-to-Text:     /api/stt/...")
    print("   • Evaluation:         /api/evaluate/...")
    print("\n🌐 Web Interfaces:")
    print("   • API Docs:           /docs")
    print("   • ReDoc:              /redoc")
    print("   • TTS Player:         /player")
    print("   • STT Interface:      /recorder")
    print("   • Evaluation UI:      /evaluate")
    print("=" * 60)
    
    yield
    
    # Shutdown
    print("\n⏹ Shutting down Quran Recitation App...")
    print("✓ Cleanup complete")


# ============================================================================
# CREATE FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Quran Recitation Evaluation API",
    description="""
## 🕌 Complete Quran Recitation System

This API provides a complete backend for Quran recitation evaluation:

### 📖 Quran Database
- Access all 114 Surahs with Arabic text
- Get individual Ayahs
- Search functionality

### 🔊 Text-to-Speech (TTS)
- Play Quran recitations aloud
- Multiple reciters (Mishary Alafasy, Al-Husary, etc.)
- Various audio quality options

### 🎤 Speech-to-Text (STT)
- Arabic speech recognition optimized for Quranic recitation
- Powered by OpenAI Whisper API
- Advanced voice activity detection

### ✅ Recitation Evaluation
- Compare user's recitation against Quran text
- Word-by-word accuracy matching
- Color-coded feedback (Green/Yellow/Red)
- Detailed accuracy scores
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ============================================================================
# MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# INCLUDE FEATURE ROUTERS
# ============================================================================

# Core Quran Database API (no prefix - main endpoints)
# TTS Feature
app.include_router(tts_router, prefix="/api/tts", tags=["Text-to-Speech"])

# STT Feature
app.include_router(stt_router, prefix="/api/stt", tags=["Speech-to-Text"])

# Evaluation Feature
app.include_router(evaluation_router, prefix="/api/evaluate", tags=["Evaluation"])


# ============================================================================
# CORE QURAN DATABASE ENDPOINTS
# ============================================================================

@app.get("/surahs", response_model=list[schemas.SurahOut], tags=["Quran Database"])
def get_all_surahs(db: Session = Depends(get_db)):
    """Get list of all 114 Surahs"""
    return crud.get_all_surahs(db)


@app.get("/surahs/{surah_id}", response_model=schemas.SurahDetailOut, tags=["Quran Database"])
def get_surah(surah_id: int, db: Session = Depends(get_db)):
    """Get a specific Surah with all its Ayahs"""
    surah = crud.get_surah_by_id(db, surah_id)
    if not surah:
        raise HTTPException(status_code=404, detail="Surah not found")
    return surah


@app.get("/ayahs/{surah_number}/{ayah_number}", response_model=schemas.AyahOut, tags=["Quran Database"])
def get_ayah(surah_number: int, ayah_number: int, db: Session = Depends(get_db)):
    """Get a specific Ayah by Surah and Ayah number"""
    ayah = crud.get_ayah(db, surah_number, ayah_number)
    if not ayah:
        raise HTTPException(status_code=404, detail="Ayah not found")
    return ayah


# ============================================================================
# HEALTH CHECK & INFO
# ============================================================================

@app.get("/", tags=["Info"])
async def root():
    """API root - shows available endpoints"""
    return {
        "app": "Quran Recitation Evaluation API",
        "version": "1.0.0",
        "features": {
            "quran_database": {
                "description": "Access Quran Surahs and Ayahs",
                "endpoints": ["/surahs", "/surahs/{id}", "/ayahs/{surah}/{ayah}"]
            },
            "text_to_speech": {
                "description": "Play Quran recitations",
                "endpoints": ["/api/tts/playback/{surah}", "/api/tts/reciters"]
            },
            "speech_to_text": {
                "description": "Transcribe Arabic recitation",
                "endpoints": ["/api/stt/transcribe", "/api/stt/health"]
            },
            "evaluation": {
                "description": "Evaluate recitation accuracy",
                "endpoints": ["/api/evaluate/recitation", "/api/evaluate/realtime"]
            }
        },
        "web_interfaces": {
            "docs": "/docs",
            "player": "/player",
            "recorder": "/recorder",
            "evaluate": "/evaluate"
        }
    }


@app.get("/health", tags=["Info"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "quran-recitation-app",
        "features": {
            "tts": "active",
            "stt": "active",
            "evaluation": "active"
        }
    }


# ============================================================================
# RUN SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
