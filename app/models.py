"""
Database Models
===============
SQLAlchemy models for Quran data storage.
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Surah(Base):
    """Surah (Chapter) model"""
    __tablename__ = "surahs"

    id = Column(Integer, primary_key=True)
    number = Column(Integer, unique=True, index=True)
    name_ar = Column(String, nullable=False)  # Arabic name
    name_en = Column(String, nullable=False)  # English name
    ayah_count = Column(Integer, nullable=False)

    # Relationship to Ayahs
    ayahs = relationship(
        "Ayah",
        back_populates="surah",
        order_by="Ayah.number",
        cascade="all, delete-orphan"
    )


class Ayah(Base):
    """Ayah (Verse) model"""
    __tablename__ = "ayahs"

    id = Column(Integer, primary_key=True)
    surah_id = Column(Integer, ForeignKey("surahs.id", ondelete="CASCADE"))
    number = Column(Integer, nullable=False)  # Ayah number within Surah
    text = Column(Text, nullable=False)  # Arabic text

    # Relationship to Surah
    surah = relationship("Surah", back_populates="ayahs")


class RecitationHistory(Base):
    """Store user's recitation history and scores"""
    __tablename__ = "recitation_history"

    id = Column(Integer, primary_key=True)
    surah_id = Column(Integer, ForeignKey("surahs.id"))
    ayah_start = Column(Integer, nullable=False)
    ayah_end = Column(Integer, nullable=False)
    accuracy_score = Column(Integer, nullable=False)  # 0-100
    transcribed_text = Column(Text)
    timestamp = Column(String)  # ISO format timestamp
    
    # Optional: user_id for multi-user support
    # user_id = Column(Integer, ForeignKey("users.id"))
