"""
Real-time Speech-to-Text Module - FIXED VERSION
Safe callback handling - no async issues
"""

import sounddevice as sd
import numpy as np
import queue
import threading
import tempfile
import os
import scipy.io.wavfile as wavfile
from typing import Callable, Optional
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Audio parameters - EXACTLY as in original
RATE = 16000
CHANNELS = 1
CHUNK_DURATION = 0.1  # 100ms chunks
MIN_SPEECH_DURATION = 1.0  # Minimum 1 second
MAX_SPEECH_DURATION = 30.0  # Maximum 30 seconds
SILENCE_DURATION = 5.0  # 5 seconds silence triggers transcription


class RealtimeSTT:
    """
    Real-time Speech-to-Text - EXACT copy of original logic
    With safe callback handling
    """
    
    def __init__(self):
        # State
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.speech_buffer = []
        
        # VAD state
        self.is_speaking = False
        self.silence_frames = 0
        
        # Callbacks (sync only - put messages in queue)
        self.callback_func = None
        self.status_callback = None
        
        # Statistics
        self.total_transcriptions = 0
        self.successful_transcriptions = 0
        
        # Stream
        self.stream = None
        self.process_thread = None
    
    def _safe_callback(self, callback, *args):
        """Safely call a callback, ignoring errors"""
        if callback:
            try:
                callback(*args)
            except Exception as e:
                print(f"Callback error (ignored): {e}")
    
    def is_speech(self, audio_chunk):
        """
        Simple speech detection using only energy - EXACTLY as original
        """
        energy = np.sqrt(np.mean(audio_chunk**2))
        # Hardcoded threshold as in original
        is_speech = energy > 0.03
        return is_speech, energy
    
    def normalize_audio(self, audio_data):
        """Normalize audio to -1 to 1 range"""
        if np.max(np.abs(audio_data)) > 0:
            return audio_data / np.max(np.abs(audio_data))
        return audio_data
    
    def audio_callback(self, indata, frames, time_info, status):
        """Audio input callback"""
        if status:
            print(f"Audio status: {status}")
        
        if self.is_listening:
            self.audio_queue.put(indata.copy())
    
    def process_audio_stream(self):
        """Process audio stream with VAD"""
        silence_frames_threshold = int(SILENCE_DURATION / CHUNK_DURATION)
        
        while self.is_listening:
            try:
                # Get audio chunk
                chunk = self.audio_queue.get(timeout=1)
                chunk = chunk.flatten()
                
                # Check for speech using VAD
                is_speech, energy = self.is_speech(chunk)
                
                if is_speech:
                    # Speech detected
                    if not self.is_speaking:
                        # Start of speech
                        self.is_speaking = True
                        self.speech_buffer = []
                        print("🎤 Speech started")
                        self._safe_callback(self.status_callback, "Speech detected")
                    
                    # Add to speech buffer
                    self.speech_buffer.append(chunk)
                    self.silence_frames = 0
                    
                    # Check if we've hit max duration
                    if len(self.speech_buffer) * CHUNK_DURATION > MAX_SPEECH_DURATION:
                        self.process_speech_buffer()
                        
                else:
                    # Silence detected
                    if self.is_speaking:
                        self.silence_frames += 1
                        self.speech_buffer.append(chunk)  # Keep adding to buffer
                        
                        # Check if silence duration exceeded
                        if self.silence_frames >= silence_frames_threshold:
                            # End of speech
                            speech_duration = len(self.speech_buffer) * CHUNK_DURATION
                            
                            if speech_duration >= MIN_SPEECH_DURATION:
                                self.process_speech_buffer()
                            else:
                                print(f"⚠ Speech too short: {speech_duration:.2f}s")
                                self.speech_buffer = []
                                self.is_speaking = False
                                self.silence_frames = 0
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Processing error: {e}")
    
    def process_speech_buffer(self):
        """Process accumulated speech buffer"""
        if not self.speech_buffer:
            return
        
        try:
            # Combine all chunks
            combined_audio = np.concatenate(self.speech_buffer)
            duration = len(combined_audio) / RATE
            
            print(f"📝 Processing speech segment ({duration:.2f}s)")
            self._safe_callback(self.status_callback, "Processing with Whisper AI...")
            
            # Just normalize
            combined_audio = self.normalize_audio(combined_audio)
            
            # Transcribe
            self.transcribe_audio(combined_audio)
            
        except Exception as e:
            print(f"Error processing speech buffer: {e}")
        finally:
            # Reset buffer
            self.speech_buffer = []
            self.is_speaking = False
            self.silence_frames = 0
    
    def transcribe_audio(self, audio_data):
        """Transcribe audio using OpenAI Whisper API"""
        try:
            self.total_transcriptions += 1
            
            # Convert to int16 for WAV
            audio_int16 = (audio_data * 32767).astype(np.int16)
            
            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            wavfile.write(temp_file.name, RATE, audio_int16)
            temp_file.close()
            
            # Transcribe with Whisper
            with open(temp_file.name, 'rb') as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language="ar",
                    response_format="verbose_json",
                    temperature=0.0
                )
                text = transcript.text
            
            # Clean up
            os.remove(temp_file.name)
            
            # Handle result
            if text and text.strip():
                self.successful_transcriptions += 1
                print(f"✓ Transcribed: {text}")
                
                # Call the callback with transcribed text
                self._safe_callback(self.callback_func, text)
                self._safe_callback(self.status_callback, "Success! Listening...")
            else:
                print("⚠ No speech detected in audio")
                self._safe_callback(self.status_callback, "No speech detected")
                
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            self._safe_callback(self.status_callback, f"Error: {str(e)}")
    
    def start(self, callback_func: Callable[[str], None]):
        """
        Start listening and transcribing
        
        Args:
            callback_func: Function to call with transcribed text
        """
        self.callback_func = callback_func
        self.is_listening = True
        
        # Reset state
        self.speech_buffer = []
        self.is_speaking = False
        self.silence_frames = 0
        
        # Clear queue
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        
        try:
            # Start audio stream
            self.stream = sd.InputStream(
                callback=self.audio_callback,
                channels=CHANNELS,
                samplerate=RATE,
                blocksize=int(RATE * CHUNK_DURATION),
                dtype=np.float32
            )
            self.stream.start()
            print("✓ Microphone started")
            
            # Start processing thread
            self.process_thread = threading.Thread(
                target=self.process_audio_stream,
                daemon=True
            )
            self.process_thread.start()
            print("✓ Processing thread started")
            
        except Exception as e:
            print(f"❌ Error starting microphone: {e}")
            self.is_listening = False
            raise
    
    def stop(self):
        """Stop listening"""
        print("⏹ Stopping transcription...")
        self.is_listening = False
        
        # Process any remaining speech
        if self.speech_buffer and self.is_speaking:
            speech_duration = len(self.speech_buffer) * CHUNK_DURATION
            if speech_duration >= MIN_SPEECH_DURATION:
                print(f"📝 Processing final speech ({speech_duration:.1f}s)")
                self.process_speech_buffer()
        
        # Stop stream
        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except:
                pass
            self.stream = None
        
        # Wait for thread
        if self.process_thread and self.process_thread.is_alive():
            self.process_thread.join(timeout=2)
        
        print("✓ Transcription stopped")
    
    def get_statistics(self):
        """Get current statistics"""
        success_rate = 0
        if self.total_transcriptions > 0:
            success_rate = (self.successful_transcriptions / self.total_transcriptions) * 100
        
        return {
            "total_transcriptions": self.total_transcriptions,
            "successful_transcriptions": self.successful_transcriptions,
            "success_rate": round(success_rate, 1)
        }
