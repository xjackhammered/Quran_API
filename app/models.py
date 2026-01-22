"""
SQLAlchemy Database Models
Quran Surah and Ayah models
"""

from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Surah(Base):
    """
    Surah (Chapter) model
    
    Represents one of the 114 chapters of the Quran
    """
    __tablename__ = "surahs"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(Integer, unique=True, index=True, nullable=False)
    name_ar = Column(String(100), nullable=False)  # Arabic name
    name_en = Column(String(100), nullable=False)  # English name
    ayah_count = Column(Integer, nullable=False)   # Number of verses

    # Relationship to Ayahs
    ayahs = relationship(
        "Ayah",
        back_populates="surah",
        order_by="Ayah.number",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Surah {self.number}: {self.name_ar}>"


class Ayah(Base):
    """
    Ayah (Verse) model
    
    Represents a single verse within a Surah
    """
    __tablename__ = "ayahs"

    id = Column(Integer, primary_key=True, index=True)
    surah_id = Column(
        Integer, 
        ForeignKey("surahs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    number = Column(Integer, nullable=False)  # Verse number within Surah
    text = Column(Text, nullable=False)       # Arabic text of the verse

    # Relationship to Surah
    surah = relationship("Surah", back_populates="ayahs")

    def __repr__(self):
        return f"<Ayah {self.surah_id}:{self.number}>"
