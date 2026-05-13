import sys
import threading
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread, pyqtSignal, QObject
from pynput import keyboard

from ui import SiriOverlay
from voice_engine import VoiceEngine
from assistant import Assistant

class Worker(QObject):
    update_state = pyqtSignal(str) # 'listening', 'speaking', 'idle', 'processing', 'wake_word'
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.manual_trigger = False
        
    def trigger_manually(self):
        self.manual_trigger = True

    def run(self):
        try:
            try:
                self.voice = VoiceEngine()
                self.assistant = Assistant()
                print("Components initialized successfully.")
            except Exception as e:
                print(f"Initialization Error: {e}")
                import traceback
                traceback.print_exc()
                return

            # Startup Greeting
            self.update_state.emit('speaking')
            self.voice.speak("System initialized. I'm Computer, Online and ready.")
            self.update_state.emit('idle')
            
            print("Computer Agent is ready. Wake word: Computer.")
            print("Hotkey: Ctrl+Shift+C. Say 'Stop' to end a conversation.")
            print("You can ask any question directly!")
            
            while self.running:
                try:
                    if self.assistant.should_exit:
                        self.running = False
                        break
                    
                    # Listen for wake word or hotkey
                    if not self.manual_trigger:
                        self.update_state.emit('wake_word')
                        self.voice.stop_background_listening()
                        wake_text = self.voice.listen_for_wake_word(timeout=None) # Wait indefinitely 
                        if not wake_text: continue
                        
                        # If the wake word detection already captured the command, use it
                        processed_wake = wake_text.lower().strip()
                        is_just_wake = False
                        for w in self.voice.wake_words:
                            if processed_wake == w:
                                is_just_wake = True
                                break
                        
                        if not is_just_wake:
                            # Check if it contains a wake word AND something else
                            has_wake = any(w in processed_wake for w in self.voice.wake_words)
                            if has_wake:
                                # Extract the command part after the wake word
                                for w in self.voice.wake_words:
                                    if w in processed_wake:
                                        initial_command = processed_wake.split(w, 1)[-1].strip()
                                        if initial_command:
                                            print(f">>> Command detected in wake phase: {initial_command}")
                                            self._process_single_command(initial_command)
                                            break
                    
                    # Enter continuous mode once triggered
                    self.manual_trigger = False
                    print(">>> Active conversation started.")
                    
                    # Reset interruption state for new session
                    self.voice._interrupted = False
                    
                    consecutive_silence = 0
                    while self.running:
                        try:
                            self.update_state.emit('listening')
                            self.voice.stop_background_listening()
                            # Reduced timeout for faster loop but check for stop keywords
                            command = self.voice.listen(timeout=5, phrase_time_limit=8)
                            
                            if command:
                                consecutive_silence = 0
                                print(f">>> Command: {command}")
                                if any(kw in command for kw in ["stop", "nothing", "that's all", "end conversation", "goodbye"]):
                                    print(">>> Active conversation ended by user.")
                                    self.update_state.emit('idle')
                                    break
                                
                                self._process_single_command(command)
                            else:
                                consecutive_silence += 1
                                # If silence occurs, just loop back to listening unless it's been a long time (e.g. 5 loops = ~25-30s)
                                if consecutive_silence > 5:
                                    print(">>> Active conversation timed out due to silence.")
                                    self.update_state.emit('idle')
                                    break
                                # Reset state to listening even if silence
                                self.update_state.emit('listening')
                                
                        except Exception as e:
                            print(f"Inner Loop Error: {e}")
                            break
                        
                        if self.assistant.should_exit:
                            self.running = False
                            break
                    
                    self.update_state.emit('idle')
                    time.sleep(0.1)
                except Exception as e:
                    print(f"Main Loop Error: {e}")
                    import traceback
                    traceback.print_exc()
                    time.sleep(1)
        except Exception as e:
            print(f"Critical Worker Error: {e}")
            import traceback
            traceback.print_exc()

    def _process_single_command(self, command):
        if not command: return
        print(f"User command: {command}")
        self.update_state.emit('processing')
        
        # Start background listener for interruption during reasoning/processing
        self.voice._interrupted = False
        self.voice.start_background_listening()
        
        try:
            response = self.assistant.process_command(command)
        except Exception as e:
            response = f"I encountered an error processing that: {e}"
        
        # Stop listener after processing is done (or if we need to speak)
        self.voice.stop_background_listening()
        time.sleep(0.1) # Give it a moment to release the mic
        
        # Check for interruption before speaking
        if self.voice._interrupted:
            print(">>> Processing interrupted by wake word.")
            self.voice._interrupted = False
            self.update_state.emit('idle')
            return

        try:
            print(f"Computer response: {response}")
        except UnicodeEncodeError:
            print(f"Computer response: {response.encode('ascii', 'replace').decode('ascii')}")
        self.update_state.emit('speaking')
        self.voice.speak(response)

    def stop(self):
        self.running = False

class HotkeyListener:
    def __init__(self, worker):
        self.worker = worker
        self.listener = None
        
    def start(self):
        def on_activate():
            self.worker.trigger_manually()
        
        hotkey = keyboard.HotKey(
            keyboard.HotKey.parse('<ctrl>+<shift>+c'),
            on_activate
        )
        
        def for_canonical(f):
            return lambda k: f(self.listener.canonical(k))
        
        self.listener = keyboard.Listener(
            on_press=for_canonical(hotkey.press),
            on_release=for_canonical(hotkey.release)
        )
        self.listener.start()
    
    def stop(self):
        if self.listener:
            self.listener.stop()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SiriOverlay()
    
    thread = QThread()
    worker = Worker()
    worker.moveToThread(thread)
    
    hotkey_listener = HotkeyListener(worker)
    
    thread.started.connect(worker.run)
    worker.update_state.connect(window.set_state)
    
    # Handle text input from Voice Access via UI
    def handle_ui_input(text):
        if worker.running:
            print(f"[Main] UI Trigger received: {text}")
            # Inject directly into processing or store for the loop
            worker.voice.interrupt() # Stop current listening if any
            threading.Thread(target=worker._process_single_command, args=(text,), daemon=True).start()

    window.text_input_received.connect(handle_ui_input)

    print("Starting thread...")
    thread.start()
    print("Starting hotkey listener...")
    hotkey_listener.start()
    print("Showing window...")
    window.show()
    print("Entering Qt event loop...")
    
    try:
        exit_code = app.exec()
    except KeyboardInterrupt:
        pass
    finally:
        worker.stop()
        hotkey_listener.stop()
        thread.quit()
        thread.wait()
        sys.exit(0)
