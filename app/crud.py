"""
CRUD Operations
===============
Database operations for Quran data.
"""

from sqlalchemy.orm import Session, joinedload
from app.models import Surah, Ayah, RecitationHistory
from typing import Optional, List
from datetime import datetime


# ============================================================================
# SURAH OPERATIONS
# ============================================================================

def get_all_surahs(db: Session) -> List[Surah]:
    """Get all 114 Surahs ordered by number"""
    return db.query(Surah).order_by(Surah.number).all()


def get_surah_by_id(db: Session, surah_id: int) -> Optional[Surah]:
    """Get a Surah by ID with all its Ayahs"""
    return (
        db.query(Surah)
        .options(joinedload(Surah.ayahs))
        .filter(Surah.id == surah_id)
        .first()
    )


def get_surah_by_number(db: Session, surah_number: int) -> Optional[Surah]:
    """Get a Surah by its number (1-114)"""
    return (
        db.query(Surah)
        .options(joinedload(Surah.ayahs))
        .filter(Surah.number == surah_number)
        .first()
    )


# ============================================================================
# AYAH OPERATIONS
# ============================================================================

def get_ayah(db: Session, surah_number: int, ayah_number: int) -> Optional[Ayah]:
    """Get a specific Ayah by Surah and Ayah number"""
    return (
        db.query(Ayah)
        .join(Surah)
        .filter(Surah.number == surah_number)
        .filter(Ayah.number == ayah_number)
        .first()
    )


def get_ayahs_range(
    db: Session, 
    surah_number: int, 
    start_ayah: int, 
    end_ayah: int
) -> List[Ayah]:
    """Get a range of Ayahs from a Surah"""
    return (
        db.query(Ayah)
        .join(Surah)
        .filter(Surah.number == surah_number)
        .filter(Ayah.number >= start_ayah)
        .filter(Ayah.number <= end_ayah)
        .order_by(Ayah.number)
        .all()
    )


def get_ayah_text_range(
    db: Session,
    surah_number: int,
    start_ayah: int,
    end_ayah: Optional[int] = None
) -> str:
    """Get combined text for a range of Ayahs"""
    if end_ayah is None:
        end_ayah = start_ayah
    
    ayahs = get_ayahs_range(db, surah_number, start_ayah, end_ayah)
    return " ".join([ayah.text for ayah in ayahs])


# ============================================================================
# RECITATION HISTORY OPERATIONS
# ============================================================================

def save_recitation_history(
    db: Session,
    surah_id: int,
    ayah_start: int,
    ayah_end: int,
    accuracy_score: int,
    transcribed_text: str = None
) -> RecitationHistory:
    """Save a recitation attempt to history"""
    record = RecitationHistory(
        surah_id=surah_id,
        ayah_start=ayah_start,
        ayah_end=ayah_end,
        accuracy_score=accuracy_score,
        transcribed_text=transcribed_text,
        timestamp=datetime.now().isoformat()
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_recitation_history(
    db: Session,
    limit: int = 50
) -> List[RecitationHistory]:
    """Get recent recitation history"""
    return (
        db.query(RecitationHistory)
        .order_by(RecitationHistory.id.desc())
        .limit(limit)
        .all()
    )


def get_surah_best_score(db: Session, surah_id: int) -> Optional[int]:
    """Get best accuracy score for a Surah"""
    result = (
        db.query(RecitationHistory.accuracy_score)
        .filter(RecitationHistory.surah_id == surah_id)
        .order_by(RecitationHistory.accuracy_score.desc())
        .first()
    )
    return result[0] if result else None
