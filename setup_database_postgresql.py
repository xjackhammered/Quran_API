"""
Quran Database Setup - PostgreSQL Version
==========================================
Creates and populates PostgreSQL database with all 114 Surahs and 6236 Ayahs.

BEFORE RUNNING:
1. Install PostgreSQL
2. Create database: CREATE DATABASE quran_app;
3. Set DATABASE_URL in .env file

Usage:
    python setup_database.py
"""

import os
import sys
import time

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ Loaded .env file")
except ImportError:
    print("Installing python-dotenv...")
    os.system(f"{sys.executable} -m pip install python-dotenv")
    from dotenv import load_dotenv
    load_dotenv()

# Check for required packages
try:
    import httpx
except ImportError:
    print("Installing httpx...")
    os.system(f"{sys.executable} -m pip install httpx")
    import httpx

try:
    import psycopg2
except ImportError:
    print("Installing psycopg2-binary...")
    os.system(f"{sys.executable} -m pip install psycopg2-binary")

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("\n" + "=" * 60)
    print("  ERROR: DATABASE_URL not found!")
    print("=" * 60)
    print("\nPlease create a .env file with:")
    print("  DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/quran_app")
    print("\nOr set it directly:")
    DATABASE_URL = input("\nEnter your DATABASE_URL: ").strip()
    if not DATABASE_URL:
        sys.exit(1)

print(f"\nDatabase URL: {DATABASE_URL[:50]}...")

# SQLAlchemy setup
Base = declarative_base()


class Surah(Base):
    """Surah (Chapter) model"""
    __tablename__ = "surahs"

    id = Column(Integer, primary_key=True)
    number = Column(Integer, unique=True, index=True)
    name_ar = Column(String(100), nullable=False)
    name_en = Column(String(100), nullable=False)
    ayah_count = Column(Integer, nullable=False)

    ayahs = relationship("Ayah", back_populates="surah", cascade="all, delete-orphan")


class Ayah(Base):
    """Ayah (Verse) model"""
    __tablename__ = "ayahs"

    id = Column(Integer, primary_key=True)
    surah_id = Column(Integer, ForeignKey("surahs.id", ondelete="CASCADE"))
    number = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)

    surah = relationship("Surah", back_populates="ayahs")


# All 114 Surahs metadata
SURAH_METADATA = [
    {"number": 1, "name_ar": "الفاتحة", "name_en": "Al-Fatiha", "ayah_count": 7},
    {"number": 2, "name_ar": "البقرة", "name_en": "Al-Baqara", "ayah_count": 286},
    {"number": 3, "name_ar": "آل عمران", "name_en": "Aal-Imran", "ayah_count": 200},
    {"number": 4, "name_ar": "النساء", "name_en": "An-Nisa", "ayah_count": 176},
    {"number": 5, "name_ar": "المائدة", "name_en": "Al-Ma'ida", "ayah_count": 120},
    {"number": 6, "name_ar": "الأنعام", "name_en": "Al-An'am", "ayah_count": 165},
    {"number": 7, "name_ar": "الأعراف", "name_en": "Al-A'raf", "ayah_count": 206},
    {"number": 8, "name_ar": "الأنفال", "name_en": "Al-Anfal", "ayah_count": 75},
    {"number": 9, "name_ar": "التوبة", "name_en": "At-Tawba", "ayah_count": 129},
    {"number": 10, "name_ar": "يونس", "name_en": "Yunus", "ayah_count": 109},
    {"number": 11, "name_ar": "هود", "name_en": "Hud", "ayah_count": 123},
    {"number": 12, "name_ar": "يوسف", "name_en": "Yusuf", "ayah_count": 111},
    {"number": 13, "name_ar": "الرعد", "name_en": "Ar-Ra'd", "ayah_count": 43},
    {"number": 14, "name_ar": "إبراهيم", "name_en": "Ibrahim", "ayah_count": 52},
    {"number": 15, "name_ar": "الحجر", "name_en": "Al-Hijr", "ayah_count": 99},
    {"number": 16, "name_ar": "النحل", "name_en": "An-Nahl", "ayah_count": 128},
    {"number": 17, "name_ar": "الإسراء", "name_en": "Al-Isra", "ayah_count": 111},
    {"number": 18, "name_ar": "الكهف", "name_en": "Al-Kahf", "ayah_count": 110},
    {"number": 19, "name_ar": "مريم", "name_en": "Maryam", "ayah_count": 98},
    {"number": 20, "name_ar": "طه", "name_en": "Ta-Ha", "ayah_count": 135},
    {"number": 21, "name_ar": "الأنبياء", "name_en": "Al-Anbiya", "ayah_count": 112},
    {"number": 22, "name_ar": "الحج", "name_en": "Al-Hajj", "ayah_count": 78},
    {"number": 23, "name_ar": "المؤمنون", "name_en": "Al-Mu'minun", "ayah_count": 118},
    {"number": 24, "name_ar": "النور", "name_en": "An-Nur", "ayah_count": 64},
    {"number": 25, "name_ar": "الفرقان", "name_en": "Al-Furqan", "ayah_count": 77},
    {"number": 26, "name_ar": "الشعراء", "name_en": "Ash-Shu'ara", "ayah_count": 227},
    {"number": 27, "name_ar": "النمل", "name_en": "An-Naml", "ayah_count": 93},
    {"number": 28, "name_ar": "القصص", "name_en": "Al-Qasas", "ayah_count": 88},
    {"number": 29, "name_ar": "العنكبوت", "name_en": "Al-Ankabut", "ayah_count": 69},
    {"number": 30, "name_ar": "الروم", "name_en": "Ar-Rum", "ayah_count": 60},
    {"number": 31, "name_ar": "لقمان", "name_en": "Luqman", "ayah_count": 34},
    {"number": 32, "name_ar": "السجدة", "name_en": "As-Sajda", "ayah_count": 30},
    {"number": 33, "name_ar": "الأحزاب", "name_en": "Al-Ahzab", "ayah_count": 73},
    {"number": 34, "name_ar": "سبأ", "name_en": "Saba", "ayah_count": 54},
    {"number": 35, "name_ar": "فاطر", "name_en": "Fatir", "ayah_count": 45},
    {"number": 36, "name_ar": "يس", "name_en": "Ya-Sin", "ayah_count": 83},
    {"number": 37, "name_ar": "الصافات", "name_en": "As-Saffat", "ayah_count": 182},
    {"number": 38, "name_ar": "ص", "name_en": "Sad", "ayah_count": 88},
    {"number": 39, "name_ar": "الزمر", "name_en": "Az-Zumar", "ayah_count": 75},
    {"number": 40, "name_ar": "غافر", "name_en": "Ghafir", "ayah_count": 85},
    {"number": 41, "name_ar": "فصلت", "name_en": "Fussilat", "ayah_count": 54},
    {"number": 42, "name_ar": "الشورى", "name_en": "Ash-Shura", "ayah_count": 53},
    {"number": 43, "name_ar": "الزخرف", "name_en": "Az-Zukhruf", "ayah_count": 89},
    {"number": 44, "name_ar": "الدخان", "name_en": "Ad-Dukhan", "ayah_count": 59},
    {"number": 45, "name_ar": "الجاثية", "name_en": "Al-Jathiya", "ayah_count": 37},
    {"number": 46, "name_ar": "الأحقاف", "name_en": "Al-Ahqaf", "ayah_count": 35},
    {"number": 47, "name_ar": "محمد", "name_en": "Muhammad", "ayah_count": 38},
    {"number": 48, "name_ar": "الفتح", "name_en": "Al-Fath", "ayah_count": 29},
    {"number": 49, "name_ar": "الحجرات", "name_en": "Al-Hujurat", "ayah_count": 18},
    {"number": 50, "name_ar": "ق", "name_en": "Qaf", "ayah_count": 45},
    {"number": 51, "name_ar": "الذاريات", "name_en": "Adh-Dhariyat", "ayah_count": 60},
    {"number": 52, "name_ar": "الطور", "name_en": "At-Tur", "ayah_count": 49},
    {"number": 53, "name_ar": "النجم", "name_en": "An-Najm", "ayah_count": 62},
    {"number": 54, "name_ar": "القمر", "name_en": "Al-Qamar", "ayah_count": 55},
    {"number": 55, "name_ar": "الرحمن", "name_en": "Ar-Rahman", "ayah_count": 78},
    {"number": 56, "name_ar": "الواقعة", "name_en": "Al-Waqi'a", "ayah_count": 96},
    {"number": 57, "name_ar": "الحديد", "name_en": "Al-Hadid", "ayah_count": 29},
    {"number": 58, "name_ar": "المجادلة", "name_en": "Al-Mujadila", "ayah_count": 22},
    {"number": 59, "name_ar": "الحشر", "name_en": "Al-Hashr", "ayah_count": 24},
    {"number": 60, "name_ar": "الممتحنة", "name_en": "Al-Mumtahina", "ayah_count": 13},
    {"number": 61, "name_ar": "الصف", "name_en": "As-Saff", "ayah_count": 14},
    {"number": 62, "name_ar": "الجمعة", "name_en": "Al-Jumu'a", "ayah_count": 11},
    {"number": 63, "name_ar": "المنافقون", "name_en": "Al-Munafiqun", "ayah_count": 11},
    {"number": 64, "name_ar": "التغابن", "name_en": "At-Taghabun", "ayah_count": 18},
    {"number": 65, "name_ar": "الطلاق", "name_en": "At-Talaq", "ayah_count": 12},
    {"number": 66, "name_ar": "التحريم", "name_en": "At-Tahrim", "ayah_count": 12},
    {"number": 67, "name_ar": "الملك", "name_en": "Al-Mulk", "ayah_count": 30},
    {"number": 68, "name_ar": "القلم", "name_en": "Al-Qalam", "ayah_count": 52},
    {"number": 69, "name_ar": "الحاقة", "name_en": "Al-Haqqa", "ayah_count": 52},
    {"number": 70, "name_ar": "المعارج", "name_en": "Al-Ma'arij", "ayah_count": 44},
    {"number": 71, "name_ar": "نوح", "name_en": "Nuh", "ayah_count": 28},
    {"number": 72, "name_ar": "الجن", "name_en": "Al-Jinn", "ayah_count": 28},
    {"number": 73, "name_ar": "المزمل", "name_en": "Al-Muzzammil", "ayah_count": 20},
    {"number": 74, "name_ar": "المدثر", "name_en": "Al-Muddaththir", "ayah_count": 56},
    {"number": 75, "name_ar": "القيامة", "name_en": "Al-Qiyama", "ayah_count": 40},
    {"number": 76, "name_ar": "الإنسان", "name_en": "Al-Insan", "ayah_count": 31},
    {"number": 77, "name_ar": "المرسلات", "name_en": "Al-Mursalat", "ayah_count": 50},
    {"number": 78, "name_ar": "النبأ", "name_en": "An-Naba", "ayah_count": 40},
    {"number": 79, "name_ar": "النازعات", "name_en": "An-Nazi'at", "ayah_count": 46},
    {"number": 80, "name_ar": "عبس", "name_en": "Abasa", "ayah_count": 42},
    {"number": 81, "name_ar": "التكوير", "name_en": "At-Takwir", "ayah_count": 29},
    {"number": 82, "name_ar": "الانفطار", "name_en": "Al-Infitar", "ayah_count": 19},
    {"number": 83, "name_ar": "المطففين", "name_en": "Al-Mutaffifin", "ayah_count": 36},
    {"number": 84, "name_ar": "الانشقاق", "name_en": "Al-Inshiqaq", "ayah_count": 25},
    {"number": 85, "name_ar": "البروج", "name_en": "Al-Buruj", "ayah_count": 22},
    {"number": 86, "name_ar": "الطارق", "name_en": "At-Tariq", "ayah_count": 17},
    {"number": 87, "name_ar": "الأعلى", "name_en": "Al-A'la", "ayah_count": 19},
    {"number": 88, "name_ar": "الغاشية", "name_en": "Al-Ghashiya", "ayah_count": 26},
    {"number": 89, "name_ar": "الفجر", "name_en": "Al-Fajr", "ayah_count": 30},
    {"number": 90, "name_ar": "البلد", "name_en": "Al-Balad", "ayah_count": 20},
    {"number": 91, "name_ar": "الشمس", "name_en": "Ash-Shams", "ayah_count": 15},
    {"number": 92, "name_ar": "الليل", "name_en": "Al-Layl", "ayah_count": 21},
    {"number": 93, "name_ar": "الضحى", "name_en": "Ad-Duha", "ayah_count": 11},
    {"number": 94, "name_ar": "الشرح", "name_en": "Ash-Sharh", "ayah_count": 8},
    {"number": 95, "name_ar": "التين", "name_en": "At-Tin", "ayah_count": 8},
    {"number": 96, "name_ar": "العلق", "name_en": "Al-Alaq", "ayah_count": 19},
    {"number": 97, "name_ar": "القدر", "name_en": "Al-Qadr", "ayah_count": 5},
    {"number": 98, "name_ar": "البينة", "name_en": "Al-Bayyina", "ayah_count": 8},
    {"number": 99, "name_ar": "الزلزلة", "name_en": "Az-Zalzala", "ayah_count": 8},
    {"number": 100, "name_ar": "العاديات", "name_en": "Al-Adiyat", "ayah_count": 11},
    {"number": 101, "name_ar": "القارعة", "name_en": "Al-Qari'a", "ayah_count": 11},
    {"number": 102, "name_ar": "التكاثر", "name_en": "At-Takathur", "ayah_count": 8},
    {"number": 103, "name_ar": "العصر", "name_en": "Al-Asr", "ayah_count": 3},
    {"number": 104, "name_ar": "الهمزة", "name_en": "Al-Humaza", "ayah_count": 9},
    {"number": 105, "name_ar": "الفيل", "name_en": "Al-Fil", "ayah_count": 5},
    {"number": 106, "name_ar": "قريش", "name_en": "Quraysh", "ayah_count": 4},
    {"number": 107, "name_ar": "الماعون", "name_en": "Al-Ma'un", "ayah_count": 7},
    {"number": 108, "name_ar": "الكوثر", "name_en": "Al-Kawthar", "ayah_count": 3},
    {"number": 109, "name_ar": "الكافرون", "name_en": "Al-Kafirun", "ayah_count": 6},
    {"number": 110, "name_ar": "النصر", "name_en": "An-Nasr", "ayah_count": 3},
    {"number": 111, "name_ar": "المسد", "name_en": "Al-Masad", "ayah_count": 5},
    {"number": 112, "name_ar": "الإخلاص", "name_en": "Al-Ikhlas", "ayah_count": 4},
    {"number": 113, "name_ar": "الفلق", "name_en": "Al-Falaq", "ayah_count": 5},
    {"number": 114, "name_ar": "الناس", "name_en": "An-Nas", "ayah_count": 6},
]


def fetch_surah_ayahs(surah_number: int) -> list:
    """Fetch ayahs for a surah from AlQuran.cloud API"""
    url = f"https://api.alquran.cloud/v1/surah/{surah_number}/quran-uthmani"
    
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "OK":
                ayahs = data["data"]["ayahs"]
                return [{"number": a["numberInSurah"], "text": a["text"]} for a in ayahs]
    except Exception as e:
        print(f"Error: {e}")
    
    return []


def test_connection(engine):
    """Test database connection"""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"\n✗ Cannot connect to database: {e}")
        print("\nPlease check:")
        print("  1. PostgreSQL is running")
        print("  2. Database 'quran_app' exists")
        print("  3. Username and password are correct")
        return False


def setup_database():
    """Create tables and populate with Quran data"""
    
    print("\n" + "=" * 60)
    print("  QURAN DATABASE SETUP (PostgreSQL)")
    print("=" * 60)
    
    # Create engine
    print("\n[0/4] Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    if not test_connection(engine):
        sys.exit(1)
    print("  ✓ Connected to PostgreSQL")
    
    # Drop and create tables
    print("\n[1/4] Creating database tables...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    print("  ✓ Tables created: surahs, ayahs")
    
    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Insert Surahs
        print("\n[2/4] Inserting 114 Surahs...")
        for surah_data in SURAH_METADATA:
            surah = Surah(
                number=surah_data["number"],
                name_ar=surah_data["name_ar"],
                name_en=surah_data["name_en"],
                ayah_count=surah_data["ayah_count"]
            )
            session.add(surah)
        session.commit()
        print("  ✓ All 114 Surahs inserted")
        
        # Fetch and insert Ayahs
        print("\n[3/4] Fetching Ayahs from AlQuran.cloud API...")
        print("  This takes 2-3 minutes. Please wait...\n")
        
        total_ayahs = 0
        failed = []
        
        for i, surah_data in enumerate(SURAH_METADATA, 1):
            surah_num = surah_data["number"]
            surah_name = surah_data["name_en"]
            
            # Get the surah from database
            surah = session.query(Surah).filter(Surah.number == surah_num).first()
            
            # Fetch ayahs from API
            progress = f"[{i:3d}/114]"
            print(f"  {progress} {surah_name:20s}", end=" ", flush=True)
            
            ayahs_data = fetch_surah_ayahs(surah_num)
            
            if ayahs_data:
                # Insert ayahs
                for ayah_data in ayahs_data:
                    ayah = Ayah(
                        surah_id=surah.id,
                        number=ayah_data["number"],
                        text=ayah_data["text"]
                    )
                    session.add(ayah)
                
                session.commit()
                total_ayahs += len(ayahs_data)
                print(f"✓ {len(ayahs_data):3d} ayahs")
            else:
                failed.append(surah_name)
                print("✗ Failed")
            
            # Small delay to avoid rate limiting
            time.sleep(0.2)
        
        # Verify
        print("\n[4/4] Verifying database...")
        surah_count = session.query(Surah).count()
        ayah_count = session.query(Ayah).count()
        
        print("\n" + "=" * 60)
        print("  ✓ DATABASE SETUP COMPLETE!")
        print("=" * 60)
        print(f"  ✓ Surahs in database: {surah_count}")
        print(f"  ✓ Ayahs in database:  {ayah_count}")
        
        if failed:
            print(f"  ⚠ Failed surahs: {', '.join(failed)}")
        
        print("=" * 60)
        
        # Sample data
        print("\n  Sample data from database:")
        sample = session.query(Ayah).join(Surah).filter(Surah.number == 1).first()
        if sample:
            print(f"  Surah 1, Ayah 1: {sample.text[:50]}...")
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    setup_database()
