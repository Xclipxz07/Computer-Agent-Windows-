import asyncio
import os
import pygame
import speech_recognition as sr
import time
import threading
from typing import List, Optional

# Constants
VOICE = "en-US-AriaNeural"
TEMP_FILE = "temp_voice.mp3"

class VoiceEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # distance / sensitivity optimizations (Maximized)
        self.recognizer.energy_threshold = 150  # Very sensitive base for distance
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.10
        self.recognizer.dynamic_energy_ratio = 1.2  # Trigger more easily
        self.recognizer.pause_threshold = 1.2   # Wait longer for natural speech gaps
        self.recognizer.non_speaking_duration = 0.5
        self.recognizer.phrase_threshold = 0.2  # Fast capture
        
        self.wake_words = ["computer", "claire", "hey computer", "hey claire"]
        # Sort by length descending to match longest phrases first (e.g. 'ask agent' before 'ask ag')
        self.wake_words.sort(key=len, reverse=True)
        self._interrupted = False
        self.mic_lock = threading.Lock()
        self.background_stop_fn = None
        
        try:
            pygame.mixer.init()
        except:
            print("Pygame mixer init failed")

    async def _speak_async(self, text):
        import edge_tts
        import random
        import string
        
        # Use a slightly more unique name to avoid permission issues
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        temp_file = f"temp_voice_{suffix}.mp3"
        
        try:
            communicate = edge_tts.Communicate(text, VOICE)
            await communicate.save(temp_file)
            
            # Re-enable background listening for interruption during speech
            self.start_background_listening()
            
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                if self._interrupted:
                    pygame.mixer.music.stop()
                    print("[Voice] Speech interrupted.")
                    break
                await asyncio.sleep(0.1)
                
            pygame.mixer.music.unload()
            self._interrupted = False
            
        except Exception as e:
            print(f"Audio playback error: {e}")
        finally:
            # STOP the listener after speaking is done
            self.stop_background_listening()
            if os.path.exists(temp_file):
                try: os.remove(temp_file)
                except: pass

    def speak(self, text):
        """Synchronous wrapper for speaking"""
        self._interrupted = False
        try:
            asyncio.run(self._speak_async(text))
        except Exception as e:
            print(f"Error speaking: {e}")

    def interrupt(self):
        """Set interruption flag"""
        self._interrupted = True

    def start_background_listening(self):
        """Starts a background thread to listen for wake words as an interruption with retry logic."""
        for attempt in range(3):
            try:
                # If already running, no need to restart
                if self.background_stop_fn:
                    return self.background_stop_fn

                # Ensure previous stop finished releasing resource
                time.sleep(0.3)

                def callback(recognizer, audio):
                    try:
                        text = recognizer.recognize_google(audio).lower()
                        if any(word in text for word in self.wake_words):
                            print(f"[Interrupt] Wake word detected in background: '{text}'")
                            self.interrupt()
                    except Exception as e:
                        # Silently fail for background recognition errors
                        pass

                with self.mic_lock:
                    with self.microphone as source:
                        # calibrate once with a decent duration
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    self.background_stop_fn = self.recognizer.listen_in_background(self.microphone, callback, phrase_time_limit=2)
                    print("[Voice] Background listener started.")
                    return self.background_stop_fn
            except Exception as e:
                print(f"[Voice] Start background listener attempt {attempt+1} failed: {e}")
                if "context manager" in str(e):
                    time.sleep(0.5)
                    continue
                break
        return None

    def stop_background_listening(self):
        """Stops the background listener if it's running"""
        # We don't lock here to allow the listener thread to finish its context if it's closing
        if self.background_stop_fn:
            try:
                self.background_stop_fn(wait_for_stop=False)
            except:
                pass
            self.background_stop_fn = None
            # Mandatory sleep to ensure Windows releases the resource
            time.sleep(0.5)

    def listen(self, timeout=5, phrase_time_limit=8):
        """Listens for audio input and returns text. Safely handles resource conflicts."""
        for _ in range(3): # Retry 3 times
            try:
                self.stop_background_listening()
                with self.mic_lock:
                    with self.microphone as source:
                        # minimal adjustment for active phase to avoid clipping start of "yes/no"
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.1)
                        audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
                        text = self.recognizer.recognize_google(audio).lower()
                        return text
            except Exception as e:
                if "context manager" in str(e):
                    time.sleep(0.5)
                    continue
                return ""
        return ""

    def listen_for_wake_word(self, timeout=None):
        """Listen specifically for wake words with resource safety."""
        for _ in range(3): # Retry 3 times
            try:
                self.stop_background_listening()
                with self.mic_lock:
                    with self.microphone as source:
                        # calibration for wake word phase
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.3)
                        audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=5)
                        text = self.recognizer.recognize_google(audio).lower()
                        for word in self.wake_words:
                            if word in text:
                                return text
                        return None
            except sr.WaitTimeoutError:
                return None
            except Exception as e:
                if "context manager" in str(e):
                    time.sleep(0.5)
                    continue
                print(f"[Voice] Wake listen error: {e}")
                return None
        return None

    def check_for_interrupt(self, text):
        """Check if text contains a wake word for interruption"""
        if not text: return False
        return any(word in text.lower() for word in self.wake_words)

if __name__ == "__main__":
    engine = VoiceEngine()
    engine.speak("Voice engine initialized.")
