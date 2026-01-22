from pydantic import BaseModel
from typing import List


class AyahOut(BaseModel):
    id: int
    number: int     # ✅ MATCHES SQLAlchemy
    text: str

    class Config:
        from_attributes = True


class SurahOut(BaseModel):
    id: int
    number: int
    name_ar: str
    name_en: str
    ayah_count: int

    class Config:
        from_attributes = True


class SurahDetailOut(SurahOut):
    ayahs: List[AyahOut]
