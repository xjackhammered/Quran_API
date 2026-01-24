# Quran Recitation Evaluation App

A comprehensive FastAPI backend for Quran recitation evaluation with Text-to-Speech and Speech-to-Text capabilities.

## Features

### Quran Database API
- Access all 114 Surahs with Arabic text
- Get individual Ayahs
- Full-text search

### Text-to-Speech (TTS)
- Play Quran recitations aloud
- 19+ male reciters (Mishary Alafasy, Al-Husary, etc.)
- Multiple audio quality options (32, 64, 128, 192 kbps)

### Speech-to-Text (STT)
- Arabic speech recognition optimized for Quranic recitation
- Powered by OpenAI Whisper API
- Advanced Voice Activity Detection (VAD)

### Recitation Evaluation
- Compare user's recitation against Quran text
- Word-by-word accuracy matching
- Color-coded feedback (Green/Yellow/Red)
- Arabic suggestions for improvement

## Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL database
- OpenAI API key (for STT feature)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and edit environment file
cp .env.example .env
# Edit .env with your DATABASE_URL and OPENAI_API_KEY

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Access the API
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## API Endpoints

### Quran Database
- `GET /surahs` - List all Surahs
- `GET /surahs/{id}` - Get Surah with Ayahs
- `GET /ayahs/{surah}/{ayah}` - Get specific Ayah

### Text-to-Speech
- `GET /api/tts/playback/{surah}` - Get playback data
- `GET /api/tts/reciters` - List reciters

### Speech-to-Text
- `POST /api/stt/transcribe` - Transcribe audio
- `GET /api/stt/health` - Service status

### Evaluation
- `POST /api/evaluate/recitation` - Evaluate text
- `POST /api/evaluate/audio` - Transcribe + evaluate
- `GET /api/evaluate/reference/{surah}/{ayah}` - Get reference text

## Project Structure

```
quran-recitation-app/
├── app/
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py              # Database operations
│   └── features/
│       ├── tts/             # Text-to-Speech feature
│       │   ├── service.py
│       │   └── router.py
│       ├── stt/             # Speech-to-Text feature
│       │   ├── service.py
│       │   └── router.py
│       └── evaluation/      # Recitation evaluation
│           ├── service.py
│           └── router.py
├── requirements.txt
├── .env.example
└── README.md
```

## Usage Examples

### Evaluate a Recitation (Python)

```python
import requests

# Evaluate transcribed text
response = requests.post(
    "http://localhost:8000/api/evaluate/recitation",
    json={
        "surah_number": 1,
        "ayah_start": 1,
        "ayah_end": 7,
        "transcribed_text": "بسم الله الرحمن الرحيم"
    }
)
result = response.json()
print(f"Accuracy: {result['overall_accuracy']}%")
```

### Combined Audio Evaluation

```python
import requests
import base64

# Read audio file
with open("recitation.wav", "rb") as f:
    audio_base64 = base64.b64encode(f.read()).decode()

# Send for evaluation
response = requests.post(
    "http://localhost:8000/api/evaluate/audio",
    json={
        "surah_number": 1,
        "ayah_start": 1,
        "audio_base64": audio_base64
    }
)
result = response.json()
print(f"Transcribed: {result['transcription']['text']}")
print(f"Accuracy: {result['evaluation']['overall_accuracy']}%")
```

### Play Surah Audio (JavaScript)

```javascript
// Fetch playback data
const response = await fetch('/api/tts/playback/1?reciter=ar.alafasy');
const data = await response.json();

// Play each ayah
for (const ayah of data.audio_urls) {
    const audio = new Audio(ayah.audio_url);
    await audio.play();
}
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| DATABASE_URL | PostgreSQL connection string | Yes |
| OPENAI_API_KEY | OpenAI API key for Whisper | Yes (for STT) |
| SAMPLE_RATE | Audio sample rate (default: 16000) | No |
| ENERGY_THRESHOLD | VAD sensitivity (default: 0.03) | No |

## License

MIT License
