"""
CRUD Operations
Database query functions for Quran data
"""

from sqlalchemy.orm import Session, joinedload
from app.models import Surah, Ayah
from typing import Optional, List


def get_all_surahs(db: Session) -> List[Surah]:
    """
    Get all Surahs ordered by number
    
    Args:
        db: Database session
    
    Returns:
        List of all Surahs
    """
    return db.query(Surah).order_by(Surah.number).all()


def get_surah_by_id(db: Session, surah_id: int) -> Optional[Surah]:
    """
    Get a Surah by ID with all its Ayahs
    
    Args:
        db: Database session
        surah_id: Surah ID
    
    Returns:
        Surah with Ayahs or None if not found
    """
    return (
        db.query(Surah)
        .options(joinedload(Surah.ayahs))
        .filter(Surah.id == surah_id)
        .first()
    )


def get_surah_by_number(db: Session, surah_number: int) -> Optional[Surah]:
    """
    Get a Surah by its number (1-114)
    
    Args:
        db: Database session
        surah_number: Surah number
    
    Returns:
        Surah with Ayahs or None if not found
    """
    return (
        db.query(Surah)
        .options(joinedload(Surah.ayahs))
        .filter(Surah.number == surah_number)
        .first()
    )


def get_ayah(db: Session, surah_id: int, ayah_number: int) -> Optional[Ayah]:
    """
    Get a specific Ayah
    
    Args:
        db: Database session
        surah_id: Surah ID
        ayah_number: Ayah number within the Surah
    
    Returns:
        Ayah or None if not found
    """
    return (
        db.query(Ayah)
        .filter(Ayah.surah_id == surah_id, Ayah.number == ayah_number)
        .first()
    )


def search_ayahs(db: Session, query: str, limit: int = 10) -> List[Ayah]:
    """
    Search Ayahs by text content
    
    Args:
        db: Database session
        query: Search query
        limit: Maximum results
    
    Returns:
        List of matching Ayahs
    """
    return (
        db.query(Ayah)
        .filter(Ayah.text.contains(query))
        .limit(limit)
        .all()
    )
