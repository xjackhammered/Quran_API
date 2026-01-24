"""
Arabic Speech-to-Text Service
=============================
Advanced Arabic STT optimized for Quranic recitation using OpenAI Whisper API.

Features:
- Voice Activity Detection (VAD)
- Audio preprocessing (normalization, noise reduction)
- Optimized for Arabic/Quranic pronunciation
"""

import os
import tempfile
import base64
import numpy as np
from typing import Optional, Tuple
from dataclasses import dataclass
from scipy import signal
import io

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# OpenAI client
try:
    from openai import OpenAI
    api_key = os.getenv("OPENAI_API_KEY", "")
    client = OpenAI(api_key=api_key) if api_key else None
    OPENAI_AVAILABLE = bool(api_key)
except ImportError:
    OPENAI_AVAILABLE = False
    client = None

# Audio parameters
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
CHANNELS = 1


@dataclass
class TranscriptionResult:
    """Result of a transcription"""
    text: str
    confidence: str
    duration: Optional[float] = None
    language: str = "ar"


class AdvancedVAD:
    """Advanced Voice Activity Detection for Arabic speech"""
    
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self.sample_rate = sample_rate
        self.energy_threshold = float(os.getenv("ENERGY_THRESHOLD", "0.03"))
    
    def calculate_energy(self, audio_chunk: np.ndarray) -> float:
        """Calculate RMS energy of audio chunk"""
        return float(np.sqrt(np.mean(audio_chunk**2)))
    
    def calculate_zcr(self, audio_chunk: np.ndarray) -> float:
        """Calculate Zero Crossing Rate"""
        signs = np.sign(audio_chunk)
        zcr = np.sum(np.abs(np.diff(signs))) / (2 * len(audio_chunk))
        return float(zcr)
    
    def is_speech(self, audio_chunk: np.ndarray) -> Tuple[bool, float]:
        """Detect if audio chunk contains speech"""
        energy = self.calculate_energy(audio_chunk)
        is_speech = energy > self.energy_threshold
        return is_speech, energy
    
    def get_speech_segments(self, audio_data: np.ndarray) -> list:
        """Extract speech segments from audio"""
        chunk_size = int(0.1 * self.sample_rate)  # 100ms chunks
        segments = []
        current_segment_start = None
        silence_frames = 0
        max_silence = 5  # 500ms of silence to end segment
        
        for i in range(0, len(audio_data), chunk_size):
            chunk = audio_data[i:i+chunk_size]
            if len(chunk) < chunk_size:
                break
            
            is_speech, _ = self.is_speech(chunk)
            
            if is_speech:
                if current_segment_start is None:
                    current_segment_start = i
                silence_frames = 0
            else:
                if current_segment_start is not None:
                    silence_frames += 1
                    if silence_frames >= max_silence:
                        segments.append((current_segment_start, i))
                        current_segment_start = None
                        silence_frames = 0
        
        # Handle last segment
        if current_segment_start is not None:
            segments.append((current_segment_start, len(audio_data)))
        
        return segments


class AudioPreprocessor:
    """Audio preprocessing for optimal Whisper performance"""
    
    @staticmethod
    def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
        """Normalize audio to -1 to 1 range"""
        max_val = np.max(np.abs(audio_data))
        if max_val > 0:
            return audio_data / max_val
        return audio_data
    
    @staticmethod
    def apply_noise_gate(audio_data: np.ndarray, threshold: float = 0.01) -> np.ndarray:
        """Apply noise gate to remove low-level noise"""
        audio_data = audio_data.copy()
        audio_data[np.abs(audio_data) < threshold] = 0
        return audio_data
    
    @staticmethod
    def apply_bandpass_filter(
        audio_data: np.ndarray, 
        sample_rate: int,
        lowcut: int = 80,
        highcut: int = 8000
    ) -> np.ndarray:
        """Apply bandpass filter for speech frequencies"""
        nyquist = sample_rate / 2
        low = lowcut / nyquist
        high = min(highcut / nyquist, 0.99)  # Ensure < 1
        
        b, a = signal.butter(4, [low, high], btype='band')
        filtered = signal.filtfilt(b, a, audio_data)
        
        return filtered
    
    @staticmethod
    def remove_dc_offset(audio_data: np.ndarray) -> np.ndarray:
        """Remove DC offset from audio"""
        return audio_data - np.mean(audio_data)
    
    @staticmethod
    def apply_pre_emphasis(audio_data: np.ndarray, coefficient: float = 0.97) -> np.ndarray:
        """Apply pre-emphasis filter to boost high frequencies"""
        return np.append(audio_data[0], audio_data[1:] - coefficient * audio_data[:-1])
    
    @classmethod
    def process_audio(
        cls, 
        audio_data: np.ndarray, 
        sample_rate: int = SAMPLE_RATE,
        full_processing: bool = True
    ) -> np.ndarray:
        """
        Full audio preprocessing pipeline
        
        Args:
            audio_data: Raw audio samples
            sample_rate: Audio sample rate
            full_processing: If True, apply all filters. If False, just normalize.
        """
        # Remove DC offset
        audio_data = cls.remove_dc_offset(audio_data)
        
        if full_processing:
            # Apply bandpass filter (speech frequencies)
            audio_data = cls.apply_bandpass_filter(audio_data, sample_rate)
            
            # Apply noise gate
            audio_data = cls.apply_noise_gate(audio_data)
            
            # Apply pre-emphasis
            audio_data = cls.apply_pre_emphasis(audio_data)
        
        # Normalize
        audio_data = cls.normalize_audio(audio_data)
        
        return audio_data


class ArabicSTTService:
    """
    Arabic Speech-to-Text Service
    
    Transcribes Arabic audio using OpenAI Whisper API with
    preprocessing optimized for Quranic recitation.
    """
    
    def __init__(self):
        self.vad = AdvancedVAD()
        self.preprocessor = AudioPreprocessor()
        self.client = client
        
        # Statistics
        self.total_transcriptions = 0
        self.successful_transcriptions = 0
    
    def _decode_base64_audio(self, audio_base64: str) -> Tuple[np.ndarray, int]:
        """Decode base64 audio to numpy array"""
        import wave
        
        audio_bytes = base64.b64decode(audio_base64)
        
        # Try to read as WAV
        try:
            with io.BytesIO(audio_bytes) as wav_io:
                with wave.open(wav_io, 'rb') as wav_file:
                    sample_rate = wav_file.getframerate()
                    n_frames = wav_file.getnframes()
                    audio_data = wav_file.readframes(n_frames)
                    
                    # Convert to numpy
                    dtype = np.int16 if wav_file.getsampwidth() == 2 else np.int32
                    audio_array = np.frombuffer(audio_data, dtype=dtype)
                    
                    # Normalize to float32
                    audio_array = audio_array.astype(np.float32) / np.iinfo(dtype).max
                    
                    return audio_array, sample_rate
        except Exception:
            # If not WAV, assume raw PCM float32
            audio_array = np.frombuffer(audio_bytes, dtype=np.float32)
            return audio_array, SAMPLE_RATE
    
    def _save_to_wav(self, audio_data: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
        """Save audio data to temporary WAV file"""
        import wave
        
        # Create temp file
        fd, filepath = tempfile.mkstemp(suffix='.wav')
        os.close(fd)
        
        # Convert to int16 for WAV
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        return filepath
    
    async def transcribe_audio(
        self,
        audio_data: np.ndarray,
        sample_rate: int = SAMPLE_RATE,
        preprocess: bool = True,
        language: str = "ar"
    ) -> TranscriptionResult:
        """
        Transcribe audio data to text
        
        Args:
            audio_data: Numpy array of audio samples
            sample_rate: Audio sample rate
            preprocess: Whether to apply preprocessing
            language: Target language code
            
        Returns:
            TranscriptionResult with transcribed text
        """
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
        
        self.total_transcriptions += 1
        
        # Preprocess audio
        if preprocess:
            audio_data = self.preprocessor.process_audio(audio_data, sample_rate)
        else:
            audio_data = self.preprocessor.normalize_audio(audio_data)
        
        # Calculate duration
        duration = len(audio_data) / sample_rate
        
        # Save to temporary WAV file
        wav_path = self._save_to_wav(audio_data, sample_rate)
        
        try:
            # Call Whisper API
            with open(wav_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    temperature=0.0,
                    prompt="بسم الله الرحمن الرحيم"  # Quranic context hint
                )
            
            text = transcript.text.strip()
            
            if text:
                self.successful_transcriptions += 1
                confidence = "high" if len(text) > 10 else "medium"
            else:
                confidence = "low"
            
            return TranscriptionResult(
                text=text,
                confidence=confidence,
                duration=duration,
                language=language
            )
            
        finally:
            # Cleanup temp file
            try:
                os.remove(wav_path)
            except:
                pass
    
    async def transcribe_base64(
        self,
        audio_base64: str,
        preprocess: bool = True,
        language: str = "ar"
    ) -> TranscriptionResult:
        """
        Transcribe base64-encoded audio
        
        Args:
            audio_base64: Base64 encoded audio (WAV or raw PCM)
            preprocess: Whether to apply preprocessing
            language: Target language
            
        Returns:
            TranscriptionResult
        """
        # Decode audio
        audio_data, sample_rate = self._decode_base64_audio(audio_base64)
        
        # Transcribe
        return await self.transcribe_audio(
            audio_data,
            sample_rate,
            preprocess,
            language
        )
    
    async def transcribe_file(
        self,
        file_path: str,
        preprocess: bool = True,
        language: str = "ar"
    ) -> TranscriptionResult:
        """Transcribe audio from file path"""
        import wave
        
        with wave.open(file_path, 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            audio_data = wav_file.readframes(n_frames)
            
            dtype = np.int16 if wav_file.getsampwidth() == 2 else np.int32
            audio_array = np.frombuffer(audio_data, dtype=dtype)
            audio_array = audio_array.astype(np.float32) / np.iinfo(dtype).max
        
        return await self.transcribe_audio(
            audio_array,
            sample_rate,
            preprocess,
            language
        )
    
    def get_stats(self) -> dict:
        """Get transcription statistics"""
        success_rate = (
            (self.successful_transcriptions / self.total_transcriptions * 100)
            if self.total_transcriptions > 0 else 0
        )
        return {
            "total_transcriptions": self.total_transcriptions,
            "successful_transcriptions": self.successful_transcriptions,
            "success_rate": round(success_rate, 1)
        }
    
    def is_available(self) -> bool:
        """Check if STT service is available"""
        return OPENAI_AVAILABLE


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_stt_instance: Optional[ArabicSTTService] = None


def get_stt_service() -> ArabicSTTService:
    """Get singleton instance of ArabicSTTService"""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = ArabicSTTService()
    return _stt_instance
