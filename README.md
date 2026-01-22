# 📖 Quran API with Advanced Arabic Speech-to-Text

A comprehensive FastAPI application combining Quran data access with state-of-the-art Arabic speech recognition optimized for Quranic recitation.

## ✨ Features

### 📖 Quran API
- Access all 114 Surahs with Arabic and English names
- Retrieve individual Ayahs (verses)
- Full Arabic text support

### 🎤 Advanced Speech-to-Text
- **OpenAI Whisper API** integration
- **Optimized for Quranic Arabic** pronunciation
- **Real-time WebSocket** transcription
- **Advanced Voice Activity Detection (VAD)**
  - Energy-based speech detection
  - Zero Crossing Rate (ZCR) analysis
  - Configurable thresholds
- **Audio Preprocessing Pipeline**
  - Bandpass filtering (80Hz - 8kHz)
  - Noise gate
  - Pre-emphasis filter
  - DC offset removal
  - Normalization
- **Multiple Preprocessing Modes**
  - Simple: Basic normalization
  - Standard: Balanced processing (recommended)
  - Advanced: Full pipeline for noisy environments

### 🖥️ Web Interfaces
- **Full Interface** (`/stt-gui/`): Complete GUI with audio visualization
- **Simple Interface** (`/stt-gui/simple`): Minimal UI
- **Test Interface** (`/stt-gui/test`): File upload testing

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd quran-stt-api

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-proj-your-key-here
```

### 3. Setup Database (PostgreSQL)

```bash
# Create database
createdb quran_app

# Or using psql
psql -U postgres -c "CREATE DATABASE quran_app;"
```

### 4. Run the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 5. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **STT GUI (Full)**: http://localhost:8000/stt-gui/
- **STT GUI (Simple)**: http://localhost:8000/stt-gui/simple
- **File Upload Test**: http://localhost:8000/stt-gui/test

## 📡 API Endpoints

### Quran Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/surahs` | GET | List all Surahs |
| `/surahs/{id}` | GET | Get Surah with Ayahs |
| `/surahs/{id}/ayahs` | GET | Get only Ayahs |
| `/surahs/{id}/ayahs/{num}` | GET | Get specific Ayah |

### Speech-to-Text Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/stt/transcribe-file` | POST | Upload WAV file |
| `/stt/transcribe-base64` | POST | Send base64 audio |
| `/stt/ws/realtime` | WebSocket | Real-time transcription |
| `/stt/analyze` | POST | Analyze audio file |
| `/stt/validate` | POST | Validate audio for STT |
| `/stt/config` | GET/PUT | View/update configuration |
| `/stt/health` | GET | Service health check |
| `/stt/sessions` | GET | Active sessions info |

## 🎛️ Configuration

All settings can be configured via environment variables:

### Audio Settings
```env
SAMPLE_RATE=16000          # Whisper's optimal rate
CHANNELS=1                 # Mono audio
CHUNK_DURATION=0.1         # 100ms chunks
```

### VAD Settings
```env
ENERGY_THRESHOLD=0.03      # Speech detection sensitivity
ZCR_THRESHOLD=0.1          # Zero crossing rate
MIN_SPEECH_FRAMES=10       # Minimum speech frames
```

### Timing Settings
```env
MIN_SPEECH_DURATION=1.0    # Minimum speech (seconds)
MAX_SPEECH_DURATION=30.0   # Maximum segment (seconds)
SILENCE_DURATION=5.0       # Silence before processing
```

### Preprocessing Settings
```env
BANDPASS_LOWCUT=80         # Low frequency cutoff (Hz)
BANDPASS_HIGHCUT=8000      # High frequency cutoff (Hz)
NOISE_GATE_THRESHOLD=0.01  # Noise gate level
PRE_EMPHASIS_COEF=0.97     # Pre-emphasis coefficient
```

## 🔌 WebSocket Real-time API

### Connect
```javascript
const ws = new WebSocket('ws://localhost:8000/stt/ws/realtime?threshold=0.03&preprocess_mode=standard');
```

### Messages from Server
```javascript
// Transcription result
{"type": "transcription", "text": "بسم الله الرحمن الرحيم", "confidence": "high"}

// Status update
{"type": "status", "message": "Listening...", "state": "listening"}

// Audio level (throttled)
{"type": "audio_level", "energy": 0.045, "is_speech": true, "level_bars": 5}

// Statistics
{"type": "statistics", "data": {"total_transcriptions": 5, "success_rate": 80.0}}

// Error
{"type": "error", "message": "Error description"}
```

### Commands to Server
```javascript
// Stop transcription
ws.send("stop");

// Update threshold
ws.send(JSON.stringify({command: "update_threshold", value: 0.05}));

// Get statistics
ws.send(JSON.stringify({command: "get_stats"}));
```

## 📁 Project Structure

```
quran-stt-api/
├── app/
│   ├── __init__.py          # Package init
│   ├── main.py              # FastAPI application
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py              # Database operations
│   ├── audio_utils.py       # Audio processing & transcription
│   ├── realtime_stt.py      # Real-time STT engine
│   ├── stt_routes.py        # STT API routes
│   └── stt_gui.py           # Web GUI interfaces
├── tests/
│   └── test_microphone.py   # Microphone testing utility
├── static/                  # Static files (if needed)
├── requirements.txt         # Python dependencies
├── .env.example            # Example configuration
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## 🎯 Usage Examples

### Python Client - File Upload

```python
import requests

# Upload WAV file
with open("audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/stt/transcribe-file",
        files={"file": f},
        params={"preprocess_mode": "standard"}
    )

result = response.json()
print(f"Transcription: {result['text']}")
```

### Python Client - Base64 Audio

```python
import requests
import base64
import numpy as np

# Create audio data
audio_data = np.random.randn(16000).astype(np.float32)  # 1 second
audio_base64 = base64.b64encode(audio_data.tobytes()).decode()

response = requests.post(
    "http://localhost:8000/stt/transcribe-base64",
    json={
        "audio_data": audio_base64,
        "sample_rate": 16000,
        "preprocess_mode": "standard"
    }
)

print(response.json())
```

### JavaScript Client - WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/stt/ws/realtime');

ws.onopen = () => console.log('Connected');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'transcription') {
        console.log('Transcribed:', data.text);
    }
};

// Stop after 30 seconds
setTimeout(() => ws.send('stop'), 30000);
```

## 🎤 Best Practices for Accuracy

### Microphone Setup
- Use a quality USB microphone (not built-in laptop mic)
- Distance: 6-12 inches from mouth
- Angle: Slightly off-axis to reduce plosives
- Gain: Set input level to 50-70%

### Environment
- Quiet room with minimal echo
- Close doors and windows
- Turn off fans/AC
- No background music

### Recitation
- Speak clearly with proper tajweed
- Maintain consistent volume
- Natural pauses between verses
- Moderate pace

### Settings
- Start with default `energy_threshold=0.03`
- Use `standard` preprocessing mode
- Adjust sensitivity based on environment

## 📊 Expected Performance

With proper setup:
- **General Arabic Speech**: 90-95% accuracy
- **Quranic Recitation**: 85-92% accuracy
- **Latency**: 2-3 seconds from speech end
- **API Cost**: ~$0.006 per minute

## 🐛 Troubleshooting

### Microphone Not Detected
```python
import sounddevice as sd
print(sd.query_devices())
```

### Audio Too Quiet
1. Increase microphone input volume (50-70%)
2. Move closer to microphone
3. Lower voice sensitivity (threshold to 0.02)

### Too Sensitive
1. Raise voice sensitivity (threshold to 0.05)
2. Use "advanced" preprocessing mode
3. Reduce background noise

### Poor Accuracy
1. Enable preprocessing
2. Speak more clearly
3. Check API key is valid
4. Verify minimum speech duration

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For issues or questions:
- Open a GitHub issue
- Check the API documentation at `/docs`
- Review the troubleshooting section

---

**Built with ❤️ for Quranic Arabic speech recognition**
