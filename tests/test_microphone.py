"""
Microphone Test Utility
Test your microphone setup before using the main application

Features:
- List audio devices
- Test microphone levels
- Test Voice Activity Detection
- Check VAD threshold settings
"""

import sounddevice as sd
import numpy as np
import time
import sys


def list_audio_devices():
    """List all available audio input devices"""
    print("\n" + "=" * 60)
    print("AVAILABLE AUDIO DEVICES")
    print("=" * 60)
    
    devices = sd.query_devices()
    input_devices = []
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            input_devices.append(i)
            print(f"\n📱 Device {i}: {device['name']}")
            print(f"   - Input Channels: {device['max_input_channels']}")
            print(f"   - Sample Rate: {device['default_samplerate']} Hz")
            print(f"   - Host API: {sd.query_hostapis(device['hostapi'])['name']}")
    
    if not input_devices:
        print("\n❌ No input devices found!")
    
    print("\n" + "=" * 60)
    return input_devices


def test_microphone(device_id=None, duration=5):
    """Test microphone input levels"""
    print("\n" + "=" * 60)
    print(f"MICROPHONE TEST - {duration} seconds")
    print("=" * 60)
    print("\n🎤 Speak into your microphone...")
    print("Watch for the audio level bars below.\n")
    
    RATE = 16000
    CHANNELS = 1
    
    max_level = 0
    
    def callback(indata, frames, time_info, status):
        nonlocal max_level
        if status:
            print(f"⚠️ Status: {status}")
        
        # Calculate audio level
        level = np.abs(indata).mean()
        energy = np.sqrt(np.mean(indata**2))
        max_level = max(max_level, energy)
        
        # Visual representation
        bars = int(min(level * 1000, 10))
        visual = "█" * bars + "░" * (10 - bars)
        
        # Color coding (using ANSI if supported)
        if energy > 0.05:
            indicator = "🟢"
        elif energy > 0.02:
            indicator = "🟡"
        else:
            indicator = "⚪"
        
        print(f"\r{indicator} Level: {visual} | RMS: {energy:.4f} | Mean: {level:.4f}", 
              end="", flush=True)
    
    try:
        kwargs = {
            'callback': callback,
            'channels': CHANNELS,
            'samplerate': RATE
        }
        if device_id is not None:
            kwargs['device'] = device_id
        
        stream = sd.InputStream(**kwargs)
        
        with stream:
            time.sleep(duration)
        
        print("\n\n✅ Microphone test complete!")
        print(f"\n📊 Maximum RMS Energy: {max_level:.4f}")
        print("\n📋 Interpretation:")
        if max_level > 0.05:
            print("   ✅ EXCELLENT - Strong voice level detected")
        elif max_level > 0.03:
            print("   ✅ GOOD - Voice level is acceptable")
        elif max_level > 0.02:
            print("   ⚠️ FAIR - Consider speaking louder or moving closer")
        elif max_level > 0.01:
            print("   ⚠️ LOW - Increase microphone gain or get closer")
        else:
            print("   ❌ POOR - Check microphone connection and settings")
        
        print(f"\n💡 Recommended ENERGY_THRESHOLD: {max(0.02, max_level * 0.5):.3f}")
        
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check if microphone is connected")
        print("   2. Check microphone permissions in system settings")
        print("   3. Try a different device ID")


def test_vad_threshold(energy_threshold=0.03, zcr_threshold=0.1):
    """Test Voice Activity Detection with current settings"""
    print("\n" + "=" * 60)
    print("VOICE ACTIVITY DETECTION TEST")
    print("=" * 60)
    print(f"\n⚙️ Settings:")
    print(f"   - Energy Threshold: {energy_threshold}")
    print(f"   - ZCR Threshold: {zcr_threshold}")
    print("\n🎤 Speak a few Arabic words or verses (10 seconds)...\n")
    
    RATE = 16000
    CHANNELS = 1
    
    speech_detected_count = 0
    total_chunks = 0
    energies = []
    
    def calculate_zcr(audio_chunk):
        """Calculate Zero Crossing Rate"""
        signs = np.sign(audio_chunk)
        zcr = np.sum(np.abs(np.diff(signs))) / (2 * len(audio_chunk))
        return zcr
    
    def callback(indata, frames, time_info, status):
        nonlocal speech_detected_count, total_chunks
        
        total_chunks += 1
        chunk = indata.flatten()
        
        # Normalize
        max_val = np.max(np.abs(chunk))
        if max_val > 0:
            chunk = chunk / max_val
        
        # Calculate features
        energy = np.sqrt(np.mean(chunk**2))
        zcr = calculate_zcr(chunk)
        energies.append(energy)
        
        # Speech detection
        is_speech = (energy > energy_threshold) and (zcr > zcr_threshold)
        
        if is_speech:
            speech_detected_count += 1
            status_icon = "✅ SPEECH"
            color = "🟢"
        else:
            status_icon = "⬜ Silence"
            color = "⚪"
        
        print(f"\r{color} {status_icon} | Energy: {energy:.4f} (>{energy_threshold}) | ZCR: {zcr:.4f} (>{zcr_threshold})", 
              end="", flush=True)
    
    try:
        stream = sd.InputStream(
            callback=callback,
            channels=CHANNELS,
            samplerate=RATE,
            blocksize=int(RATE * 0.1)
        )
        
        with stream:
            time.sleep(10)
        
        detection_rate = (speech_detected_count / total_chunks) * 100 if total_chunks > 0 else 0
        avg_energy = np.mean(energies) if energies else 0
        max_energy = np.max(energies) if energies else 0
        
        print(f"\n\n✅ VAD Test Complete!")
        print(f"\n📊 Results:")
        print(f"   - Total chunks: {total_chunks}")
        print(f"   - Speech detected: {speech_detected_count} chunks")
        print(f"   - Detection rate: {detection_rate:.1f}%")
        print(f"   - Average energy: {avg_energy:.4f}")
        print(f"   - Maximum energy: {max_energy:.4f}")
        
        print(f"\n📋 Interpretation:")
        if detection_rate > 50:
            print(f"   ✅ EXCELLENT - Voice is clearly detected")
        elif detection_rate > 30:
            print(f"   ✅ GOOD - Voice detected, may need minor adjustment")
        elif detection_rate > 10:
            print(f"   ⚠️ FAIR - Increase microphone volume or lower threshold")
        else:
            print(f"   ❌ POOR - Voice not detected well")
            print(f"   💡 Try lowering ENERGY_THRESHOLD to {max(0.01, avg_energy * 0.8):.3f}")
        
    except Exception as e:
        print(f"\n\n❌ Error: {e}")


def continuous_monitor(device_id=None):
    """Continuously monitor microphone with real-time stats"""
    print("\n" + "=" * 60)
    print("CONTINUOUS MICROPHONE MONITOR")
    print("=" * 60)
    print("\n🎤 Press Ctrl+C to stop...\n")
    
    RATE = 16000
    CHANNELS = 1
    
    stats = {
        'min_energy': float('inf'),
        'max_energy': 0,
        'samples': 0
    }
    
    def callback(indata, frames, time_info, status):
        chunk = indata.flatten()
        energy = np.sqrt(np.mean(chunk**2))
        
        stats['samples'] += 1
        stats['min_energy'] = min(stats['min_energy'], energy)
        stats['max_energy'] = max(stats['max_energy'], energy)
        
        bars = int(min(energy * 200, 20))
        visual = "▓" * bars + "░" * (20 - bars)
        
        print(f"\r[{visual}] Energy: {energy:.4f} | Min: {stats['min_energy']:.4f} | Max: {stats['max_energy']:.4f}", 
              end="", flush=True)
    
    try:
        kwargs = {
            'callback': callback,
            'channels': CHANNELS,
            'samplerate': RATE,
            'blocksize': int(RATE * 0.1)
        }
        if device_id is not None:
            kwargs['device'] = device_id
        
        stream = sd.InputStream(**kwargs)
        
        with stream:
            while True:
                time.sleep(0.1)
                
    except KeyboardInterrupt:
        print("\n\n⏹️ Monitoring stopped")
        print(f"\n📊 Session Statistics:")
        print(f"   - Samples: {stats['samples']}")
        print(f"   - Min Energy: {stats['min_energy']:.4f}")
        print(f"   - Max Energy: {stats['max_energy']:.4f}")
        print(f"   - Recommended Threshold: {stats['max_energy'] * 0.4:.4f}")


def main():
    """Main menu"""
    print("\n" + "=" * 60)
    print("🎤 AUDIO SETUP TEST UTILITY")
    print("For Quran API Speech-to-Text")
    print("=" * 60)
    
    while True:
        print("\n📋 Options:")
        print("  1. List available audio devices")
        print("  2. Test microphone (5 seconds)")
        print("  3. Test Voice Activity Detection (10 seconds)")
        print("  4. Test specific device")
        print("  5. Continuous monitor (Ctrl+C to stop)")
        print("  6. Custom VAD threshold test")
        print("  7. Exit")
        
        choice = input("\n👉 Select option (1-7): ").strip()
        
        if choice == "1":
            list_audio_devices()
        
        elif choice == "2":
            test_microphone(duration=5)
        
        elif choice == "3":
            test_vad_threshold()
        
        elif choice == "4":
            devices = list_audio_devices()
            if devices:
                device_id = input("\n👉 Enter device ID to test: ").strip()
                try:
                    device_id = int(device_id)
                    test_microphone(device_id=device_id, duration=5)
                except ValueError:
                    print("❌ Invalid device ID")
        
        elif choice == "5":
            continuous_monitor()
        
        elif choice == "6":
            try:
                threshold = input("👉 Enter energy threshold (default 0.03): ").strip()
                threshold = float(threshold) if threshold else 0.03
                test_vad_threshold(energy_threshold=threshold)
            except ValueError:
                print("❌ Invalid threshold value")
        
        elif choice == "7":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option, try again")


if __name__ == "__main__":
    main()
