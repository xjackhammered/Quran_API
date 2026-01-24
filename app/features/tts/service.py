"""
Quran Text-to-Speech Service
============================
This module provides functionality to play Quran recitations aloud.
It fetches audio from AlQuran.cloud API which provides high-quality recitations.

Features:
- Get list of all 114 Surahs with metadata
- Get available reciters
- Play/stream audio for entire Surah or specific Ayahs
- Support for multiple reciters and audio quality options
"""

import httpx
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel
from dataclasses import dataclass
import asyncio


# ============================================================================
# QURAN METADATA - All 114 Surahs
# ============================================================================

SURAH_DATA = [
    {"number": 1, "name": "الفاتحة", "englishName": "Al-Fatiha", "englishNameTranslation": "The Opening", "numberOfAyahs": 7, "revelationType": "Meccan"},
    {"number": 2, "name": "البقرة", "englishName": "Al-Baqara", "englishNameTranslation": "The Cow", "numberOfAyahs": 286, "revelationType": "Medinan"},
    {"number": 3, "name": "آل عمران", "englishName": "Aal-Imran", "englishNameTranslation": "The Family of Imran", "numberOfAyahs": 200, "revelationType": "Medinan"},
    {"number": 4, "name": "النساء", "englishName": "An-Nisa", "englishNameTranslation": "The Women", "numberOfAyahs": 176, "revelationType": "Medinan"},
    {"number": 5, "name": "المائدة", "englishName": "Al-Ma'ida", "englishNameTranslation": "The Table Spread", "numberOfAyahs": 120, "revelationType": "Medinan"},
    {"number": 6, "name": "الأنعام", "englishName": "Al-An'am", "englishNameTranslation": "The Cattle", "numberOfAyahs": 165, "revelationType": "Meccan"},
    {"number": 7, "name": "الأعراف", "englishName": "Al-A'raf", "englishNameTranslation": "The Heights", "numberOfAyahs": 206, "revelationType": "Meccan"},
    {"number": 8, "name": "الأنفال", "englishName": "Al-Anfal", "englishNameTranslation": "The Spoils of War", "numberOfAyahs": 75, "revelationType": "Medinan"},
    {"number": 9, "name": "التوبة", "englishName": "At-Tawba", "englishNameTranslation": "The Repentance", "numberOfAyahs": 129, "revelationType": "Medinan"},
    {"number": 10, "name": "يونس", "englishName": "Yunus", "englishNameTranslation": "Jonah", "numberOfAyahs": 109, "revelationType": "Meccan"},
    {"number": 11, "name": "هود", "englishName": "Hud", "englishNameTranslation": "Hud", "numberOfAyahs": 123, "revelationType": "Meccan"},
    {"number": 12, "name": "يوسف", "englishName": "Yusuf", "englishNameTranslation": "Joseph", "numberOfAyahs": 111, "revelationType": "Meccan"},
    {"number": 13, "name": "الرعد", "englishName": "Ar-Ra'd", "englishNameTranslation": "The Thunder", "numberOfAyahs": 43, "revelationType": "Medinan"},
    {"number": 14, "name": "إبراهيم", "englishName": "Ibrahim", "englishNameTranslation": "Abraham", "numberOfAyahs": 52, "revelationType": "Meccan"},
    {"number": 15, "name": "الحجر", "englishName": "Al-Hijr", "englishNameTranslation": "The Rocky Tract", "numberOfAyahs": 99, "revelationType": "Meccan"},
    {"number": 16, "name": "النحل", "englishName": "An-Nahl", "englishNameTranslation": "The Bee", "numberOfAyahs": 128, "revelationType": "Meccan"},
    {"number": 17, "name": "الإسراء", "englishName": "Al-Isra", "englishNameTranslation": "The Night Journey", "numberOfAyahs": 111, "revelationType": "Meccan"},
    {"number": 18, "name": "الكهف", "englishName": "Al-Kahf", "englishNameTranslation": "The Cave", "numberOfAyahs": 110, "revelationType": "Meccan"},
    {"number": 19, "name": "مريم", "englishName": "Maryam", "englishNameTranslation": "Mary", "numberOfAyahs": 98, "revelationType": "Meccan"},
    {"number": 20, "name": "طه", "englishName": "Ta-Ha", "englishNameTranslation": "Ta-Ha", "numberOfAyahs": 135, "revelationType": "Meccan"},
    {"number": 21, "name": "الأنبياء", "englishName": "Al-Anbiya", "englishNameTranslation": "The Prophets", "numberOfAyahs": 112, "revelationType": "Meccan"},
    {"number": 22, "name": "الحج", "englishName": "Al-Hajj", "englishNameTranslation": "The Pilgrimage", "numberOfAyahs": 78, "revelationType": "Medinan"},
    {"number": 23, "name": "المؤمنون", "englishName": "Al-Mu'minun", "englishNameTranslation": "The Believers", "numberOfAyahs": 118, "revelationType": "Meccan"},
    {"number": 24, "name": "النور", "englishName": "An-Nur", "englishNameTranslation": "The Light", "numberOfAyahs": 64, "revelationType": "Medinan"},
    {"number": 25, "name": "الفرقان", "englishName": "Al-Furqan", "englishNameTranslation": "The Criterion", "numberOfAyahs": 77, "revelationType": "Meccan"},
    {"number": 26, "name": "الشعراء", "englishName": "Ash-Shu'ara", "englishNameTranslation": "The Poets", "numberOfAyahs": 227, "revelationType": "Meccan"},
    {"number": 27, "name": "النمل", "englishName": "An-Naml", "englishNameTranslation": "The Ant", "numberOfAyahs": 93, "revelationType": "Meccan"},
    {"number": 28, "name": "القصص", "englishName": "Al-Qasas", "englishNameTranslation": "The Stories", "numberOfAyahs": 88, "revelationType": "Meccan"},
    {"number": 29, "name": "العنكبوت", "englishName": "Al-Ankabut", "englishNameTranslation": "The Spider", "numberOfAyahs": 69, "revelationType": "Meccan"},
    {"number": 30, "name": "الروم", "englishName": "Ar-Rum", "englishNameTranslation": "The Romans", "numberOfAyahs": 60, "revelationType": "Meccan"},
    {"number": 31, "name": "لقمان", "englishName": "Luqman", "englishNameTranslation": "Luqman", "numberOfAyahs": 34, "revelationType": "Meccan"},
    {"number": 32, "name": "السجدة", "englishName": "As-Sajda", "englishNameTranslation": "The Prostration", "numberOfAyahs": 30, "revelationType": "Meccan"},
    {"number": 33, "name": "الأحزاب", "englishName": "Al-Ahzab", "englishNameTranslation": "The Combined Forces", "numberOfAyahs": 73, "revelationType": "Medinan"},
    {"number": 34, "name": "سبأ", "englishName": "Saba", "englishNameTranslation": "Sheba", "numberOfAyahs": 54, "revelationType": "Meccan"},
    {"number": 35, "name": "فاطر", "englishName": "Fatir", "englishNameTranslation": "Originator", "numberOfAyahs": 45, "revelationType": "Meccan"},
    {"number": 36, "name": "يس", "englishName": "Ya-Sin", "englishNameTranslation": "Ya-Sin", "numberOfAyahs": 83, "revelationType": "Meccan"},
    {"number": 37, "name": "الصافات", "englishName": "As-Saffat", "englishNameTranslation": "Those who set the Ranks", "numberOfAyahs": 182, "revelationType": "Meccan"},
    {"number": 38, "name": "ص", "englishName": "Sad", "englishNameTranslation": "The Letter Sad", "numberOfAyahs": 88, "revelationType": "Meccan"},
    {"number": 39, "name": "الزمر", "englishName": "Az-Zumar", "englishNameTranslation": "The Troops", "numberOfAyahs": 75, "revelationType": "Meccan"},
    {"number": 40, "name": "غافر", "englishName": "Ghafir", "englishNameTranslation": "The Forgiver", "numberOfAyahs": 85, "revelationType": "Meccan"},
    {"number": 41, "name": "فصلت", "englishName": "Fussilat", "englishNameTranslation": "Explained in Detail", "numberOfAyahs": 54, "revelationType": "Meccan"},
    {"number": 42, "name": "الشورى", "englishName": "Ash-Shura", "englishNameTranslation": "The Consultation", "numberOfAyahs": 53, "revelationType": "Meccan"},
    {"number": 43, "name": "الزخرف", "englishName": "Az-Zukhruf", "englishNameTranslation": "The Ornaments of Gold", "numberOfAyahs": 89, "revelationType": "Meccan"},
    {"number": 44, "name": "الدخان", "englishName": "Ad-Dukhan", "englishNameTranslation": "The Smoke", "numberOfAyahs": 59, "revelationType": "Meccan"},
    {"number": 45, "name": "الجاثية", "englishName": "Al-Jathiya", "englishNameTranslation": "The Crouching", "numberOfAyahs": 37, "revelationType": "Meccan"},
    {"number": 46, "name": "الأحقاف", "englishName": "Al-Ahqaf", "englishNameTranslation": "The Wind-Curved Sandhills", "numberOfAyahs": 35, "revelationType": "Meccan"},
    {"number": 47, "name": "محمد", "englishName": "Muhammad", "englishNameTranslation": "Muhammad", "numberOfAyahs": 38, "revelationType": "Medinan"},
    {"number": 48, "name": "الفتح", "englishName": "Al-Fath", "englishNameTranslation": "The Victory", "numberOfAyahs": 29, "revelationType": "Medinan"},
    {"number": 49, "name": "الحجرات", "englishName": "Al-Hujurat", "englishNameTranslation": "The Rooms", "numberOfAyahs": 18, "revelationType": "Medinan"},
    {"number": 50, "name": "ق", "englishName": "Qaf", "englishNameTranslation": "The Letter Qaf", "numberOfAyahs": 45, "revelationType": "Meccan"},
    {"number": 51, "name": "الذاريات", "englishName": "Adh-Dhariyat", "englishNameTranslation": "The Winnowing Winds", "numberOfAyahs": 60, "revelationType": "Meccan"},
    {"number": 52, "name": "الطور", "englishName": "At-Tur", "englishNameTranslation": "The Mount", "numberOfAyahs": 49, "revelationType": "Meccan"},
    {"number": 53, "name": "النجم", "englishName": "An-Najm", "englishNameTranslation": "The Star", "numberOfAyahs": 62, "revelationType": "Meccan"},
    {"number": 54, "name": "القمر", "englishName": "Al-Qamar", "englishNameTranslation": "The Moon", "numberOfAyahs": 55, "revelationType": "Meccan"},
    {"number": 55, "name": "الرحمن", "englishName": "Ar-Rahman", "englishNameTranslation": "The Beneficent", "numberOfAyahs": 78, "revelationType": "Medinan"},
    {"number": 56, "name": "الواقعة", "englishName": "Al-Waqi'a", "englishNameTranslation": "The Inevitable", "numberOfAyahs": 96, "revelationType": "Meccan"},
    {"number": 57, "name": "الحديد", "englishName": "Al-Hadid", "englishNameTranslation": "The Iron", "numberOfAyahs": 29, "revelationType": "Medinan"},
    {"number": 58, "name": "المجادلة", "englishName": "Al-Mujadila", "englishNameTranslation": "The Pleading Woman", "numberOfAyahs": 22, "revelationType": "Medinan"},
    {"number": 59, "name": "الحشر", "englishName": "Al-Hashr", "englishNameTranslation": "The Exile", "numberOfAyahs": 24, "revelationType": "Medinan"},
    {"number": 60, "name": "الممتحنة", "englishName": "Al-Mumtahina", "englishNameTranslation": "She that is to be examined", "numberOfAyahs": 13, "revelationType": "Medinan"},
    {"number": 61, "name": "الصف", "englishName": "As-Saff", "englishNameTranslation": "The Ranks", "numberOfAyahs": 14, "revelationType": "Medinan"},
    {"number": 62, "name": "الجمعة", "englishName": "Al-Jumu'a", "englishNameTranslation": "The Congregation, Friday", "numberOfAyahs": 11, "revelationType": "Medinan"},
    {"number": 63, "name": "المنافقون", "englishName": "Al-Munafiqun", "englishNameTranslation": "The Hypocrites", "numberOfAyahs": 11, "revelationType": "Medinan"},
    {"number": 64, "name": "التغابن", "englishName": "At-Taghabun", "englishNameTranslation": "The Mutual Disillusion", "numberOfAyahs": 18, "revelationType": "Medinan"},
    {"number": 65, "name": "الطلاق", "englishName": "At-Talaq", "englishNameTranslation": "The Divorce", "numberOfAyahs": 12, "revelationType": "Medinan"},
    {"number": 66, "name": "التحريم", "englishName": "At-Tahrim", "englishNameTranslation": "The Prohibition", "numberOfAyahs": 12, "revelationType": "Medinan"},
    {"number": 67, "name": "الملك", "englishName": "Al-Mulk", "englishNameTranslation": "The Sovereignty", "numberOfAyahs": 30, "revelationType": "Meccan"},
    {"number": 68, "name": "القلم", "englishName": "Al-Qalam", "englishNameTranslation": "The Pen", "numberOfAyahs": 52, "revelationType": "Meccan"},
    {"number": 69, "name": "الحاقة", "englishName": "Al-Haqqa", "englishNameTranslation": "The Reality", "numberOfAyahs": 52, "revelationType": "Meccan"},
    {"number": 70, "name": "المعارج", "englishName": "Al-Ma'arij", "englishNameTranslation": "The Ascending Stairways", "numberOfAyahs": 44, "revelationType": "Meccan"},
    {"number": 71, "name": "نوح", "englishName": "Nuh", "englishNameTranslation": "Noah", "numberOfAyahs": 28, "revelationType": "Meccan"},
    {"number": 72, "name": "الجن", "englishName": "Al-Jinn", "englishNameTranslation": "The Jinn", "numberOfAyahs": 28, "revelationType": "Meccan"},
    {"number": 73, "name": "المزمل", "englishName": "Al-Muzzammil", "englishNameTranslation": "The Enshrouded One", "numberOfAyahs": 20, "revelationType": "Meccan"},
    {"number": 74, "name": "المدثر", "englishName": "Al-Muddaththir", "englishNameTranslation": "The Cloaked One", "numberOfAyahs": 56, "revelationType": "Meccan"},
    {"number": 75, "name": "القيامة", "englishName": "Al-Qiyama", "englishNameTranslation": "The Resurrection", "numberOfAyahs": 40, "revelationType": "Meccan"},
    {"number": 76, "name": "الإنسان", "englishName": "Al-Insan", "englishNameTranslation": "The Man", "numberOfAyahs": 31, "revelationType": "Medinan"},
    {"number": 77, "name": "المرسلات", "englishName": "Al-Mursalat", "englishNameTranslation": "The Emissaries", "numberOfAyahs": 50, "revelationType": "Meccan"},
    {"number": 78, "name": "النبأ", "englishName": "An-Naba", "englishNameTranslation": "The Tidings", "numberOfAyahs": 40, "revelationType": "Meccan"},
    {"number": 79, "name": "النازعات", "englishName": "An-Nazi'at", "englishNameTranslation": "Those who drag forth", "numberOfAyahs": 46, "revelationType": "Meccan"},
    {"number": 80, "name": "عبس", "englishName": "Abasa", "englishNameTranslation": "He Frowned", "numberOfAyahs": 42, "revelationType": "Meccan"},
    {"number": 81, "name": "التكوير", "englishName": "At-Takwir", "englishNameTranslation": "The Overthrowing", "numberOfAyahs": 29, "revelationType": "Meccan"},
    {"number": 82, "name": "الانفطار", "englishName": "Al-Infitar", "englishNameTranslation": "The Cleaving", "numberOfAyahs": 19, "revelationType": "Meccan"},
    {"number": 83, "name": "المطففين", "englishName": "Al-Mutaffifin", "englishNameTranslation": "The Defrauding", "numberOfAyahs": 36, "revelationType": "Meccan"},
    {"number": 84, "name": "الانشقاق", "englishName": "Al-Inshiqaq", "englishNameTranslation": "The Sundering", "numberOfAyahs": 25, "revelationType": "Meccan"},
    {"number": 85, "name": "البروج", "englishName": "Al-Buruj", "englishNameTranslation": "The Mansions of the Stars", "numberOfAyahs": 22, "revelationType": "Meccan"},
    {"number": 86, "name": "الطارق", "englishName": "At-Tariq", "englishNameTranslation": "The Morning Star", "numberOfAyahs": 17, "revelationType": "Meccan"},
    {"number": 87, "name": "الأعلى", "englishName": "Al-A'la", "englishNameTranslation": "The Most High", "numberOfAyahs": 19, "revelationType": "Meccan"},
    {"number": 88, "name": "الغاشية", "englishName": "Al-Ghashiya", "englishNameTranslation": "The Overwhelming", "numberOfAyahs": 26, "revelationType": "Meccan"},
    {"number": 89, "name": "الفجر", "englishName": "Al-Fajr", "englishNameTranslation": "The Dawn", "numberOfAyahs": 30, "revelationType": "Meccan"},
    {"number": 90, "name": "البلد", "englishName": "Al-Balad", "englishNameTranslation": "The City", "numberOfAyahs": 20, "revelationType": "Meccan"},
    {"number": 91, "name": "الشمس", "englishName": "Ash-Shams", "englishNameTranslation": "The Sun", "numberOfAyahs": 15, "revelationType": "Meccan"},
    {"number": 92, "name": "الليل", "englishName": "Al-Layl", "englishNameTranslation": "The Night", "numberOfAyahs": 21, "revelationType": "Meccan"},
    {"number": 93, "name": "الضحى", "englishName": "Ad-Duhaa", "englishNameTranslation": "The Morning Hours", "numberOfAyahs": 11, "revelationType": "Meccan"},
    {"number": 94, "name": "الشرح", "englishName": "Ash-Sharh", "englishNameTranslation": "The Relief", "numberOfAyahs": 8, "revelationType": "Meccan"},
    {"number": 95, "name": "التين", "englishName": "At-Tin", "englishNameTranslation": "The Fig", "numberOfAyahs": 8, "revelationType": "Meccan"},
    {"number": 96, "name": "العلق", "englishName": "Al-Alaq", "englishNameTranslation": "The Clot", "numberOfAyahs": 19, "revelationType": "Meccan"},
    {"number": 97, "name": "القدر", "englishName": "Al-Qadr", "englishNameTranslation": "The Power", "numberOfAyahs": 5, "revelationType": "Meccan"},
    {"number": 98, "name": "البينة", "englishName": "Al-Bayyina", "englishNameTranslation": "The Clear Proof", "numberOfAyahs": 8, "revelationType": "Medinan"},
    {"number": 99, "name": "الزلزلة", "englishName": "Az-Zalzala", "englishNameTranslation": "The Earthquake", "numberOfAyahs": 8, "revelationType": "Medinan"},
    {"number": 100, "name": "العاديات", "englishName": "Al-Adiyat", "englishNameTranslation": "The Courser", "numberOfAyahs": 11, "revelationType": "Meccan"},
    {"number": 101, "name": "القارعة", "englishName": "Al-Qari'a", "englishNameTranslation": "The Calamity", "numberOfAyahs": 11, "revelationType": "Meccan"},
    {"number": 102, "name": "التكاثر", "englishName": "At-Takathur", "englishNameTranslation": "The Rivalry in world increase", "numberOfAyahs": 8, "revelationType": "Meccan"},
    {"number": 103, "name": "العصر", "englishName": "Al-Asr", "englishNameTranslation": "The Declining Day", "numberOfAyahs": 3, "revelationType": "Meccan"},
    {"number": 104, "name": "الهمزة", "englishName": "Al-Humaza", "englishNameTranslation": "The Traducer", "numberOfAyahs": 9, "revelationType": "Meccan"},
    {"number": 105, "name": "الفيل", "englishName": "Al-Fil", "englishNameTranslation": "The Elephant", "numberOfAyahs": 5, "revelationType": "Meccan"},
    {"number": 106, "name": "قريش", "englishName": "Quraysh", "englishNameTranslation": "Quraysh", "numberOfAyahs": 4, "revelationType": "Meccan"},
    {"number": 107, "name": "الماعون", "englishName": "Al-Ma'un", "englishNameTranslation": "The Small Kindnesses", "numberOfAyahs": 7, "revelationType": "Meccan"},
    {"number": 108, "name": "الكوثر", "englishName": "Al-Kawthar", "englishNameTranslation": "The Abundance", "numberOfAyahs": 3, "revelationType": "Meccan"},
    {"number": 109, "name": "الكافرون", "englishName": "Al-Kafirun", "englishNameTranslation": "The Disbelievers", "numberOfAyahs": 6, "revelationType": "Meccan"},
    {"number": 110, "name": "النصر", "englishName": "An-Nasr", "englishNameTranslation": "The Divine Support", "numberOfAyahs": 3, "revelationType": "Medinan"},
    {"number": 111, "name": "المسد", "englishName": "Al-Masad", "englishNameTranslation": "The Palm Fiber", "numberOfAyahs": 5, "revelationType": "Meccan"},
    {"number": 112, "name": "الإخلاص", "englishName": "Al-Ikhlas", "englishNameTranslation": "The Sincerity", "numberOfAyahs": 4, "revelationType": "Meccan"},
    {"number": 113, "name": "الفلق", "englishName": "Al-Falaq", "englishNameTranslation": "The Daybreak", "numberOfAyahs": 5, "revelationType": "Meccan"},
    {"number": 114, "name": "الناس", "englishName": "An-Nas", "englishNameTranslation": "Mankind", "numberOfAyahs": 6, "revelationType": "Meccan"},
]


# ============================================================================
# RECITERS DATA - Available Audio Reciters with Gender Categories
# ============================================================================

RECITERS = [
    # ===== MALE RECITERS =====
    {
        "identifier": "ar.alafasy",
        "name": "Mishary Rashid Alafasy",
        "arabicName": "مشاري راشد العفاسي",
        "language": "ar",
        "bitrates": [192, 128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.abdurrahmaansudais",
        "name": "Abdurrahmaan As-Sudais",
        "arabicName": "عبدالرحمن السديس",
        "language": "ar",
        "bitrates": [192, 128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.abdullahbasfar",
        "name": "Abdullah Basfar",
        "arabicName": "عبدالله بصفر",
        "language": "ar",
        "bitrates": [192, 128, 64, 32],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.abdulsamad",
        "name": "AbdulBaset AbdulSamad",
        "arabicName": "عبدالباسط عبدالصمد",
        "language": "ar",
        "bitrates": [192, 128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.ahmedajamy",
        "name": "Ahmed ibn Ali al-Ajamy",
        "arabicName": "أحمد بن علي العجمي",
        "language": "ar",
        "bitrates": [128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.husary",
        "name": "Mahmoud Khalil Al-Husary",
        "arabicName": "محمود خليل الحصري",
        "language": "ar",
        "bitrates": [128],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.husarymujawwad",
        "name": "Mahmoud Khalil Al-Husary (Mujawwad)",
        "arabicName": "محمود خليل الحصري - مجود",
        "language": "ar",
        "bitrates": [128, 64],
        "style": "Mujawwad",
        "gender": "male"
    },
    {
        "identifier": "ar.hudhaify",
        "name": "Ali Al-Hudhaify",
        "arabicName": "علي الحذيفي",
        "language": "ar",
        "bitrates": [128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.ibrahimakhdar",
        "name": "Ibrahim Al-Akhdar",
        "arabicName": "إبراهيم الأخضر",
        "language": "ar",
        "bitrates": [32],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.mahermuaiqly",
        "name": "Maher Al Muaiqly",
        "arabicName": "ماهر المعيقلي",
        "language": "ar",
        "bitrates": [128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.minshawi",
        "name": "Mohamed Siddiq al-Minshawi",
        "arabicName": "محمد صديق المنشاوي",
        "language": "ar",
        "bitrates": [128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.minshawimujawwad",
        "name": "Mohamed Siddiq al-Minshawi (Mujawwad)",
        "arabicName": "محمد صديق المنشاوي - مجود",
        "language": "ar",
        "bitrates": [64],
        "style": "Mujawwad",
        "gender": "male"
    },
    {
        "identifier": "ar.muhammadayyoub",
        "name": "Muhammad Ayyoub",
        "arabicName": "محمد أيوب",
        "language": "ar",
        "bitrates": [128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.muhammadjibreel",
        "name": "Muhammad Jibreel",
        "arabicName": "محمد جبريل",
        "language": "ar",
        "bitrates": [128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.shaatree",
        "name": "Abu Bakr Ash-Shaatree",
        "arabicName": "أبو بكر الشاطري",
        "language": "ar",
        "bitrates": [128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.shuraym",
        "name": "Saud Ash-Shuraim",
        "arabicName": "سعود الشريم",
        "language": "ar",
        "bitrates": [128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    # NEW MALE RECITERS
    {
        "identifier": "ar.khalilaljalil",
        "name": "Khalid Al-Jalil",
        "arabicName": "خالد الجليل",
        "language": "ar",
        "bitrates": [128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.nasserqatami",
        "name": "Nasser Al-Qatami",
        "arabicName": "ناصر القطامي",
        "language": "ar",
        "bitrates": [128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    {
        "identifier": "ar.yasseraldossari",
        "name": "Yasser Al-Dossari",
        "arabicName": "ياسر الدوسري",
        "language": "ar",
        "bitrates": [128, 64],
        "style": "Murattal",
        "gender": "male"
    },
    
    # ===== FEMALE RECITERS =====
    # Note: These use external sources (not AlQuran.cloud API)
    # Audio URLs are from alternative CDN sources
    {
        "identifier": "female.mariaulfah",
        "name": "Maria Ulfah",
        "arabicName": "ماريا أولفة",
        "language": "ar",
        "bitrates": [128],
        "style": "Murattal",
        "gender": "female",
        "source": "qurancentral",
        "note": "Indonesian female reciter - International Quran competition winner"
    },
    {
        "identifier": "female.sumayyahedaya",
        "name": "Sumayya Eddeeb",
        "arabicName": "سمية الديب",
        "language": "ar",
        "bitrates": [128],
        "style": "Murattal",
        "gender": "female",
        "source": "external",
        "note": "Egyptian female reciter"
    },
    {
        "identifier": "female.faridaalnaboulsi",
        "name": "Farida Al-Naboulsi",
        "arabicName": "فريدة النابلسي",
        "language": "ar",
        "bitrates": [128],
        "style": "Murattal",
        "gender": "female",
        "source": "external",
        "note": "Syrian female reciter"
    },
]


# Helper function to filter reciters by gender
def get_reciters_by_gender(gender: str = None) -> list:
    """
    Get reciters filtered by gender.
    
    Args:
        gender: 'male', 'female', or None for all
    
    Returns:
        List of reciters
    """
    if gender is None:
        return RECITERS
    return [r for r in RECITERS if r.get("gender") == gender]


def get_male_reciters() -> list:
    """Get all male reciters"""
    return get_reciters_by_gender("male")


def get_female_reciters() -> list:
    """Get all female reciters"""
    return get_reciters_by_gender("female")


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class AudioBitrate(str, Enum):
    HIGH = "192"
    MEDIUM = "128"
    LOW = "64"
    LOWEST = "32"


class SurahInfo(BaseModel):
    number: int
    name: str
    englishName: str
    englishNameTranslation: str
    numberOfAyahs: int
    revelationType: str


class ReciterInfo(BaseModel):
    identifier: str
    name: str
    arabicName: str
    language: str
    bitrates: List[int]
    style: str
    gender: str = "male"
    source: Optional[str] = None
    note: Optional[str] = None


class AyahAudio(BaseModel):
    ayah_number: int
    ayah_number_in_surah: int
    text: str
    audio_url: str
    audio_secondary: List[str] = []


class SurahAudio(BaseModel):
    surah: SurahInfo
    reciter: ReciterInfo
    ayahs: List[AyahAudio]
    full_surah_audio_url: Optional[str] = None


class PlaybackInfo(BaseModel):
    """Information needed to play audio in frontend"""
    surah_number: int
    surah_name: str
    surah_name_arabic: str
    reciter_name: str
    total_ayahs: int
    audio_urls: List[Dict[str, Any]]  # List of {ayah_number, text, audio_url}
    full_surah_url: Optional[str] = None


# ============================================================================
# QURAN TTS SERVICE CLASS
# ============================================================================

class QuranTTSService:
    """
    Service to fetch and manage Quran audio recitations.
    Uses AlQuran.cloud API for audio data.
    """
    
    BASE_API_URL = "https://api.alquran.cloud/v1"
    CDN_BASE_URL = "https://cdn.islamic.network/quran/audio"
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        await self.client.aclose()
    
    # -------------------------------------------------------------------------
    # Surah Methods
    # -------------------------------------------------------------------------
    
    def get_all_surahs(self) -> List[SurahInfo]:
        """Get list of all 114 Surahs with metadata"""
        return [SurahInfo(**surah) for surah in SURAH_DATA]
    
    def get_surah_info(self, surah_number: int) -> Optional[SurahInfo]:
        """Get info for a specific Surah"""
        if 1 <= surah_number <= 114:
            return SurahInfo(**SURAH_DATA[surah_number - 1])
        return None
    
    def search_surahs(self, query: str) -> List[SurahInfo]:
        """Search surahs by name (Arabic or English)"""
        query_lower = query.lower()
        results = []
        for surah in SURAH_DATA:
            if (query_lower in surah["englishName"].lower() or 
                query_lower in surah["englishNameTranslation"].lower() or
                query in surah["name"]):
                results.append(SurahInfo(**surah))
        return results
    
    # -------------------------------------------------------------------------
    # Reciter Methods
    # -------------------------------------------------------------------------
    
    def get_all_reciters(self, gender: Optional[str] = None) -> List[ReciterInfo]:
        """
        Get list of all available reciters, optionally filtered by gender.
        
        Args:
            gender: 'male', 'female', or None for all
        """
        if gender:
            filtered = [r for r in RECITERS if r.get("gender") == gender]
            return [ReciterInfo(**reciter) for reciter in filtered]
        return [ReciterInfo(**reciter) for reciter in RECITERS]
    
    def get_male_reciters(self) -> List[ReciterInfo]:
        """Get all male reciters"""
        return self.get_all_reciters(gender="male")
    
    def get_female_reciters(self) -> List[ReciterInfo]:
        """Get all female reciters"""
        return self.get_all_reciters(gender="female")
    
    def get_reciter_info(self, identifier: str) -> Optional[ReciterInfo]:
        """Get info for a specific reciter"""
        for reciter in RECITERS:
            if reciter["identifier"] == identifier:
                return ReciterInfo(**reciter)
        return None
    
    # -------------------------------------------------------------------------
    # Audio Fetching Methods
    # -------------------------------------------------------------------------
    
    async def get_surah_audio(
        self, 
        surah_number: int, 
        reciter: str = "ar.alafasy",
        bitrate: int = 128
    ) -> Optional[SurahAudio]:
        """
        Fetch audio URLs for an entire Surah.
        
        Args:
            surah_number: Surah number (1-114)
            reciter: Reciter identifier (default: ar.alafasy for Mishary Alafasy)
            bitrate: Audio quality (192, 128, 64, 32)
        
        Returns:
            SurahAudio object with all ayah audio URLs
        """
        if not 1 <= surah_number <= 114:
            return None
        
        try:
            # Fetch from API
            url = f"{self.BASE_API_URL}/surah/{surah_number}/{reciter}"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] != 200:
                return None
            
            surah_data = data["data"]
            surah_info = self.get_surah_info(surah_number)
            reciter_info = self.get_reciter_info(reciter)
            
            if not surah_info or not reciter_info:
                return None
            
            ayahs = []
            for ayah in surah_data["ayahs"]:
                # Build CDN URLs for different bitrates
                ayah_number = ayah["number"]  # Global ayah number (1-6236)
                secondary_urls = [
                    f"{self.CDN_BASE_URL}/{br}/{reciter}/{ayah_number}.mp3"
                    for br in [192, 128, 64] if br != bitrate
                ]
                
                ayahs.append(AyahAudio(
                    ayah_number=ayah_number,
                    ayah_number_in_surah=ayah["numberInSurah"],
                    text=ayah["text"],
                    audio_url=ayah.get("audio", f"{self.CDN_BASE_URL}/{bitrate}/{reciter}/{ayah_number}.mp3"),
                    audio_secondary=secondary_urls
                ))
            
            return SurahAudio(
                surah=surah_info,
                reciter=reciter_info,
                ayahs=ayahs,
                full_surah_audio_url=None  # Can be added if needed
            )
            
        except Exception as e:
            print(f"Error fetching surah audio: {e}")
            return None
    
    async def get_ayah_audio(
        self,
        surah_number: int,
        ayah_number: int,
        reciter: str = "ar.alafasy",
        bitrate: int = 128
    ) -> Optional[AyahAudio]:
        """
        Fetch audio URL for a specific Ayah.
        
        Args:
            surah_number: Surah number (1-114)
            ayah_number: Ayah number within the Surah
            reciter: Reciter identifier
            bitrate: Audio quality
        
        Returns:
            AyahAudio object with audio URL
        """
        try:
            url = f"{self.BASE_API_URL}/ayah/{surah_number}:{ayah_number}/{reciter}"
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            if data["code"] != 200:
                return None
            
            ayah_data = data["data"]
            global_number = ayah_data["number"]
            
            secondary_urls = [
                f"{self.CDN_BASE_URL}/{br}/{reciter}/{global_number}.mp3"
                for br in [192, 128, 64] if br != bitrate
            ]
            
            return AyahAudio(
                ayah_number=global_number,
                ayah_number_in_surah=ayah_data["numberInSurah"],
                text=ayah_data["text"],
                audio_url=ayah_data.get("audio", f"{self.CDN_BASE_URL}/{bitrate}/{reciter}/{global_number}.mp3"),
                audio_secondary=secondary_urls
            )
            
        except Exception as e:
            print(f"Error fetching ayah audio: {e}")
            return None
    
    async def get_ayah_range_audio(
        self,
        surah_number: int,
        start_ayah: int,
        end_ayah: int,
        reciter: str = "ar.alafasy",
        bitrate: int = 128
    ) -> List[AyahAudio]:
        """
        Fetch audio URLs for a range of Ayahs.
        
        Args:
            surah_number: Surah number (1-114)
            start_ayah: Starting ayah number
            end_ayah: Ending ayah number
            reciter: Reciter identifier
            bitrate: Audio quality
        
        Returns:
            List of AyahAudio objects
        """
        surah_info = self.get_surah_info(surah_number)
        if not surah_info:
            return []
        
        # Validate range
        start_ayah = max(1, start_ayah)
        end_ayah = min(surah_info.numberOfAyahs, end_ayah)
        
        if start_ayah > end_ayah:
            return []
        
        # Fetch full surah and filter
        surah_audio = await self.get_surah_audio(surah_number, reciter, bitrate)
        if not surah_audio:
            return []
        
        return [
            ayah for ayah in surah_audio.ayahs
            if start_ayah <= ayah.ayah_number_in_surah <= end_ayah
        ]
    
    # -------------------------------------------------------------------------
    # Playback Helper Methods
    # -------------------------------------------------------------------------
    
    async def get_playback_info(
        self,
        surah_number: int,
        reciter: str = "ar.alafasy",
        bitrate: int = 128,
        start_ayah: Optional[int] = None,
        end_ayah: Optional[int] = None
    ) -> Optional[PlaybackInfo]:
        """
        Get all information needed to play a Surah in the frontend.
        
        This is the main method to use for the TTS feature.
        Returns a simplified object with all audio URLs ready to play.
        """
        surah_audio = await self.get_surah_audio(surah_number, reciter, bitrate)
        if not surah_audio:
            return None
        
        reciter_info = self.get_reciter_info(reciter)
        
        # Filter ayahs if range specified
        ayahs = surah_audio.ayahs
        if start_ayah is not None or end_ayah is not None:
            start = start_ayah or 1
            end = end_ayah or surah_audio.surah.numberOfAyahs
            ayahs = [a for a in ayahs if start <= a.ayah_number_in_surah <= end]
        
        audio_urls = [
            {
                "ayah_number": ayah.ayah_number_in_surah,
                "global_ayah_number": ayah.ayah_number,
                "text": ayah.text,
                "audio_url": ayah.audio_url,
                "audio_fallbacks": ayah.audio_secondary
            }
            for ayah in ayahs
        ]
        
        return PlaybackInfo(
            surah_number=surah_number,
            surah_name=surah_audio.surah.englishName,
            surah_name_arabic=surah_audio.surah.name,
            reciter_name=reciter_info.name if reciter_info else reciter,
            total_ayahs=len(ayahs),
            audio_urls=audio_urls,
            full_surah_url=surah_audio.full_surah_audio_url
        )
    
    def get_direct_audio_url(
        self,
        global_ayah_number: int,
        reciter: str = "ar.alafasy",
        bitrate: int = 128
    ) -> str:
        """
        Get direct CDN URL for an ayah audio without API call.
        
        Args:
            global_ayah_number: Global ayah number (1-6236)
            reciter: Reciter identifier
            bitrate: Audio quality
        
        Returns:
            Direct CDN URL for the audio file
        """
        return f"{self.CDN_BASE_URL}/{bitrate}/{reciter}/{global_ayah_number}.mp3"
    
    def get_playback_info_offline(
        self,
        surah_number: int,
        reciter: str = "ar.alafasy",
        bitrate: int = 128,
        start_ayah: Optional[int] = None,
        end_ayah: Optional[int] = None
    ) -> Optional[PlaybackInfo]:
        """
        Get playback info WITHOUT making API calls.
        Uses pre-calculated global ayah numbers and CDN URLs.
        
        This is useful when the API is unavailable or for faster response.
        Note: This won't include Arabic text (use API version for text).
        """
        surah_info = self.get_surah_info(surah_number)
        if not surah_info:
            return None
        
        reciter_info = self.get_reciter_info(reciter)
        
        # Calculate starting global ayah number for this surah
        global_start = 1
        for i in range(surah_number - 1):
            global_start += SURAH_DATA[i]["numberOfAyahs"]
        
        # Determine ayah range
        start = start_ayah or 1
        end = end_ayah or surah_info.numberOfAyahs
        
        audio_urls = []
        for ayah_in_surah in range(start, end + 1):
            global_num = global_start + ayah_in_surah - 1
            audio_urls.append({
                "ayah_number": ayah_in_surah,
                "global_ayah_number": global_num,
                "text": "",  # No text without API call
                "audio_url": f"{self.CDN_BASE_URL}/{bitrate}/{reciter}/{global_num}.mp3",
                "audio_fallbacks": [
                    f"{self.CDN_BASE_URL}/{br}/{reciter}/{global_num}.mp3"
                    for br in [192, 128, 64] if br != bitrate
                ]
            })
        
        return PlaybackInfo(
            surah_number=surah_number,
            surah_name=surah_info.englishName,
            surah_name_arabic=surah_info.name,
            reciter_name=reciter_info.name if reciter_info else reciter,
            total_ayahs=len(audio_urls),
            audio_urls=audio_urls,
            full_surah_url=None
        )


# ============================================================================
# HELPER FUNCTIONS FOR GLOBAL AYAH NUMBERS
# ============================================================================

def get_global_ayah_number(surah_number: int, ayah_in_surah: int) -> int:
    """
    Convert surah:ayah to global ayah number (1-6236).
    
    Example: Surah 2, Ayah 255 (Ayat Al-Kursi) = Global Ayah 262
    """
    if not 1 <= surah_number <= 114:
        raise ValueError(f"Invalid surah number: {surah_number}")
    
    global_number = 0
    for i in range(surah_number - 1):
        global_number += SURAH_DATA[i]["numberOfAyahs"]
    
    surah_total_ayahs = SURAH_DATA[surah_number - 1]["numberOfAyahs"]
    if not 1 <= ayah_in_surah <= surah_total_ayahs:
        raise ValueError(f"Invalid ayah number {ayah_in_surah} for Surah {surah_number}")
    
    return global_number + ayah_in_surah


def get_surah_ayah_from_global(global_number: int) -> tuple[int, int]:
    """
    Convert global ayah number to surah:ayah.
    
    Example: Global Ayah 262 = Surah 2, Ayah 255
    """
    if not 1 <= global_number <= 6236:
        raise ValueError(f"Invalid global ayah number: {global_number}")
    
    cumulative = 0
    for surah in SURAH_DATA:
        if cumulative + surah["numberOfAyahs"] >= global_number:
            ayah_in_surah = global_number - cumulative
            return (surah["number"], ayah_in_surah)
        cumulative += surah["numberOfAyahs"]
    
    raise ValueError(f"Could not find surah for global number: {global_number}")


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_service_instance: Optional[QuranTTSService] = None

def get_quran_tts_service() -> QuranTTSService:
    """Get singleton instance of QuranTTSService"""
    global _service_instance
    if _service_instance is None:
        _service_instance = QuranTTSService()
    return _service_instance
