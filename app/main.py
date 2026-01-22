"""
Quran API with Speech-to-Text - Main Application
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import get_db
from app import crud, schemas
from app.stt_routes import router as stt_router
from app.stt_gui import router as gui_router

app = FastAPI(
    title="Quran API with Speech-to-Text",
    description="Quran data + Arabic STT optimized for Quranic recitation",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stt_router)
app.include_router(gui_router)


@app.get("/")
async def root():
    """API root"""
    return {
        "message": "Quran API with Speech-to-Text",
        "endpoints": {
            "quran": "/surahs",
            "stt_gui": "/stt-gui/",
            "stt_test": "/stt-gui/test",
            "stt_websocket": "ws://host/stt/ws/realtime",
            "docs": "/docs"
        }
    }


@app.get("/surahs", response_model=list[schemas.SurahOut])
def read_surahs(db: Session = Depends(get_db)):
    """Get all Surahs"""
    return crud.get_all_surahs(db)


@app.get("/surahs/{surah_id}", response_model=schemas.SurahDetailOut)
def read_surah(surah_id: int, db: Session = Depends(get_db)):
    """Get a Surah with its Ayahs"""
    surah = crud.get_surah_by_id(db, surah_id)
    if not surah:
        raise HTTPException(status_code=404, detail="Surah not found")
    return surah


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
