from sqlalchemy.orm import Session, joinedload
from app.models import Surah


def get_all_surahs(db: Session):
    return db.query(Surah).order_by(Surah.number).all()


def get_surah_by_id(db, surah_id: int):
    return (
        db.query(Surah)
        .options(joinedload(Surah.ayahs))
        .filter(Surah.id == surah_id)
        .first()
    )

