"""
Audio Utilities - Simplified version matching original
"""

import os
import tempfile
import numpy as np
import scipy.io.wavfile as wavfile
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Audio parameters
RATE = 16000
CHANNELS = 1


def normalize_audio(audio_data):
    """Normalize audio to -1 to 1 range"""
    if np.max(np.abs(audio_data)) > 0:
        return audio_data / np.max(np.abs(audio_data))
    return audio_data


def transcribe_audio(audio_data: np.ndarray, sample_rate: int = 16000) -> dict:
    """
    Transcribe audio using OpenAI Whisper API
    """
    try:
        # Normalize
        audio_data = normalize_audio(audio_data)
        
        # Convert to int16
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        wavfile.write(temp_file.name, sample_rate, audio_int16)
        temp_file.close()
        
        # Transcribe
        with open(temp_file.name, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ar",
                response_format="text"
            )
        
        # Cleanup
        os.remove(temp_file.name)
        
        return {
            "success": True,
            "text": transcript.strip() if transcript else "",
            "error": None
        }
        
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": str(e)
        }


def process_audio_base64(audio_base64: str, sample_rate: int = 16000) -> dict:
    """Process base64 encoded audio"""
    import base64
    
    try:
        audio_bytes = base64.b64decode(audio_base64)
        audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
        return transcribe_audio(audio_data, sample_rate)
    except Exception as e:
        return {
            "success": False,
            "text": "",
            "error": f"Failed to decode: {str(e)}"
        }
