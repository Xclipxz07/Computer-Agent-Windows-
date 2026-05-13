import speech_recognition as sr
import time

def debug_voice_sensitivity():
    recognizer = sr.Recognizer()
    microphone = sr.Microphone()
    
    print("--- Voice Detection Debugger ---")
    print("1. Checking Microphone...")
    with microphone as source:
        print(f"   Adjusting for ambient noise (3 seconds)...")
        recognizer.adjust_for_ambient_noise(source, duration=3)
        print(f"   Current Energy Threshold: {recognizer.energy_threshold}")
        
    print("\n2. Monitoring Levels (Live)...")
    print("   Please speak normally. Watching for 10 seconds.")
    start_time = time.time()
    try:
        while time.time() - start_time < 10:
            with microphone as source:
                # We can't easily see live levels from sr.Recognizer without hacking a bit
                # but we can try to captures phrases.
                print("   Listening...")
                try:
                    audio = recognizer.listen(source, timeout=2, phrase_time_limit=3)
                    print("   Caught something! Processing...")
                    text = recognizer.recognize_google(audio)
                    print(f"   Detected: '{text}'")
                except sr.WaitTimeoutError:
                    print("   (Silence / No phrase detected)")
                except sr.UnknownValueError:
                    print("   (Audio heard but not understood)")
                except Exception as e:
                    print(f"   Error: {e}")
    except KeyboardInterrupt:
        pass

    print("\n3. Suggestions:")
    if recognizer.energy_threshold > 1000:
        print("   - High Energy Threshold detected. Your environment might be too noisy.")
    if recognizer.energy_threshold < 50:
        print("   - Very Low Energy Threshold. Microphone might be too quiet or muted.")
    print("   - Ensure you have a stable internet connection (required for Google Speech API).")
    print("   - Try moving the microphone closer or adjusting Windows Microphone Boost.")

if __name__ == "__main__":
    debug_voice_sensitivity()
