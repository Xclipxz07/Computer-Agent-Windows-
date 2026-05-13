import os
import subprocess
import datetime
import webbrowser
import re
import time
import json
import sys
import threading
from typing import Optional, Dict, Any
try:
    import psutil
except ImportError:
    psutil = None

# Lazy load constants
CACHE_FILE = "app_cache.json"
DATA_FILE = "assistant_data.json"

class Assistant:
    def __init__(self):
        self.context = None
        self.app_cache = self._load_app_cache()
        self.opened_apps = {}  # Track opened apps
        
        # Data storage
        self.data = self._load_data()
        self.notes = self.data.get("notes", [])
        self.lists = self.data.get("lists", {})
        self.alarms = self.data.get("alarms", [])
        self.reminders = self.data.get("reminders", [])
        
        # System control state - initialized on demand
        self._volume_interface = None
        self.current_volume = None
        self.current_brightness = 50
        
        # Mode tracking
        self.advanced_mode = True
        self.vision_mode = False
        from ollama_integration import OllamaIntegration
        self.ollama = OllamaIntegration()
        self.vision = None
        
        # State management for unknown command fallback
        self.pending_command = None
        
        # Exit flag
        self.should_exit = False
        
        # Background threads
        import threading
        self._ensure_voice_access_running()
        threading.Thread(target=self._build_app_cache, daemon=True).start()
        threading.Thread(target=self._scheduler_loop, daemon=True).start()

    def _ensure_voice_access_running(self):
        """Ensures Windows Voice Access is launched, safely."""
        import platform
        if platform.system() != "Windows":
            return

        try:
            # Voice Access is primarily a Windows 11 (22H2+) feature
            # Standard platform.release() for Win11 is often '10' with a high build number,
            # but we can try to launch it anyway and catch failure.
            print("[System] Attempting to launch Windows Voice Access for improved detection...")
            cmd = "start ms-voiceaccess:"
            subprocess.run(cmd, shell=True, capture_output=True, text=True)
            print("[System] Voice Access command sent. (Requires Windows 11 22H2+)")
        except Exception as e:
            print(f"[Info] Voice Access could not be launched: {e}")

    def _load_data(self) -> Dict[str, Any]:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except: pass
        return {"notes": [], "lists": {}, "alarms": [], "reminders": []}

    def _save_data(self):
        try:
            self.data = {
                "notes": self.notes,
                "lists": self.lists,
                "alarms": self.alarms,
                "reminders": self.reminders
            }
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f)
        except: pass

    def _load_app_cache(self) -> Dict[str, str]:
        """Load app cache from file for instant startup"""
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_app_cache(self):
        """Save app cache to file"""
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.app_cache, f)
        except:
            pass

    def _init_volume_interface(self):
        """Lazy initialization of pycaw"""
        if self._volume_interface:
            return True
        try:
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            
            devices = AudioUtilities.GetSpeakers()
            if not devices: return False
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self._volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
            return True
        except Exception as e:
            print(f"[Error] Volume interface init failed: {e}")
            return False

    def _get_current_volume(self) -> int:
        """Read actual system volume"""
        if not self._init_volume_interface():
            return 50
        try:
            current = self._volume_interface.GetMasterVolumeLevelScalar()
            val = int(current * 100)
            self.current_volume = val
            return val
        except Exception as e:
            print(f"[Error] Could not read volume: {e}")
            return 50

    def _build_app_cache(self):
        """Scans Start Menu folders AND UWP apps via PowerShell."""
        new_cache = {}
        # 1. Standard Shortcuts
        paths = [
            os.path.expanduser(r"~\AppData\Roaming\Microsoft\Windows\Start Menu\Programs"),
            r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs"
        ]
        for path in paths:
            if not os.path.exists(path): continue
            for root, dirs, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(".lnk"):
                        name = file.lower().replace(".lnk", "")
                        new_cache[name] = os.path.join(root, file)
        
        # 2. UWP / Store Apps
        try:
            cmd = r'powershell "Get-StartApps | ConvertTo-Json"'
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=5)
            if result.returncode == 0:
                apps = json.loads(result.stdout)
                if isinstance(apps, list):
                    for app in apps:
                        name = app.get("Name", "").lower()
                        appid = app.get("AppID", "")
                        if name and appid:
                             new_cache[name] = f"shell:AppsFolder\\{appid}"
        except: pass

        self.app_cache.update(new_cache)
        self._save_app_cache()
        print(f"[System] App cache updated. Total apps: {len(self.app_cache)}")

    def process_command(self, command):
        if not command: return "I didn't hear anything."
        command = command.lower().strip()
        print(f"[Action] Processing: '{command}'")

        # --- Exit Logic ---
        if any(kw in command for kw in ["stop the app", "stop listening", "quit computer", "exit computer", "goodbye computer"]):
            self.should_exit = True
            return "Closing down. Goodbye!"

        # --- Explicit Google Search ---
        if any(kw in command for kw in ["google search", "search google"]):
            query = command.replace("google search", "").replace("search google", "").replace("for", "").strip()
            if query:
                return self._web_search(query)
            return "What would you like me to search for on Google?"

        # --- System Commands Priority ---
        system_keywords = [
            "open", "launch", "close", "stop running", "volume", "sound", "brightness", 
            "wifi", "wi-fi", "internet", "bluetooth", "time", "date", "lock", "mute", 
            "battery", "cpu", "ram", "memory", "alarm", "timer", "remind", "note", 
            "list", "screenshot", "calculate", "tip", "play", "song", "weather", 
            "score", "calendar", "email", "directions", "traffic", "flight",
            "airplane mode", "focus mode"
        ]
        
        # If it matches a system keyword, let the system logic handle it
        is_system = False
        for kw in system_keywords:
            if kw in command:
                is_system = True
                break
        
        # Mode tracking switching keywords
        mode_keywords = ["activate", "enable", "disable", "turn on", "turn off", "use advanced", "use reasoning", "use vision", "stop advanced", "stop vision"]
        
        # If not a system command, and not mode switching, and not exit, it might be something we don't know
        # We'll check for explicit mode commands first
        
        if any(kw in command for kw in ["activate advanced mode", "enable advanced mode", "use advanced mode", "use reasoning mode", "turn on advanced mode"]):
            return self._activate_advanced_mode()
        
        if any(kw in command for kw in ["activate vision mode", "enable vision mode", "use vision mode"]):
            return self._activate_vision_mode()
        
        if any(kw in command for kw in ["disable advanced mode", "turn off advanced mode", "stop advanced mode"]):
            return self._deactivate_advanced_mode()
        
        if any(kw in command for kw in ["disable vision mode", "turn off vision mode", "stop vision mode"]):
            return self._deactivate_vision_mode()

        # --- Active Contexts ---
        if self.context == 'volume':
             if self._handle_relative_volume(command): return "Volume adjusted."
             nums = re.findall(r'\d+', command)
             if nums:
                 self.set_volume(int(nums[0]))
                 self.context = None
                 return f"Volume set to {nums[0]} percent."
             if "cancel" in command: self.context = None; return "Canceled."

        elif self.context == 'close_app':
            if "cancel" in command: self.context = None; return "Canceled."
            res = self._close_app(command)
            self.context = None
            return res

        elif self.context == 'ollama_after_search':
            # Affirmative -> Go to Ollama
            if any(kw in command for kw in ["yes", "ollama", "yeah", "sure", "ok", "okay", "advanced", "do it", "yep", "yup", "please", "confirm"]):
                res = self._query_ollama(self.pending_command)
                self.context = None
                self.pending_command = None
                return res
            # Negative -> Do nothing else
            elif any(kw in command for kw in ["no", "dont", "do not", "nope", "nada", "negative", "cancel", "stop"]):
                self.context = None
                self.pending_command = None
                return "Okay, I've opened the search results for you."
            else:
                return "Do you want me to work with Ollama for more details?"

        # --- Productivity & Info (New) ---
        
        # Alarms & Timers
        if "alarm" in command:
            if "delete" in command or "clear" in command or "remove" in command:
                return self._clear_alarms()
            return self._set_alarm(command)
        
        if "timer" in command:
            return self._set_timer(command)

        # Reminders
        if "remind" in command:
            return self._add_reminder(command)

        # Notes & Lists
        if "note" in command:
            if "read" in command or "show" in command: return self._read_notes()
            return self._create_note(command)
            
        if "list" in command:
            if "add" in command: return self._add_to_list(command)
            return self._read_list(command)

        # Screenshots
        if "screenshot" in command:
            return self._take_screenshot()

        # Calculation
        if any(kw in command for kw in ["tip", "calculate", "percent", "plus", "divided by"]):
            return self._calculate(command)

        # Media
        if "play" in command and any(kw in command for kw in ["music", "song", "jazz", "rock"]):
            return self._play_music(command)
            
        if "song" in command and any(kw in command for kw in ["what", "identify", "this"]):
            return self._identify_song()

        # Information Retrieval (Weather, Sports, etc.)
        if "weather" in command: return self._get_weather(command)
        if "score" in command or "game" in command: return self._get_sports(command)
        if "calendar" in command: return self._check_calendar()
        if "email" in command: return self._check_emails()

        # Travel & Navigation
        if "directions" in command or "way to" in command: 
            return self._get_directions(command)
        if "traffic" in command: 
            return self._get_traffic(command)
        
        # System & Travel
        if "battery" in command: return self._get_battery_status()
        if any(kw in command for kw in ["cpu", "ram", "memory", "system info"]): return self._get_system_info()
        if "restaurant" in command or "find a" in command: return self._find_places(command)
        if "flight" in command: return self._check_flight(command)

        # --- Core System Commands ---
        
        # 1. Time/Date
        if "time" in command and "set" not in command:
            return f"The current time is {datetime.datetime.now().strftime('%I:%M %p')}."
        if ("date" in command or "day" in command) and "set" not in command:
            return f"Today is {datetime.datetime.now().strftime('%A, %B %d, %Y')}."

        # 2. App Launching (Control Panel Fix)
        if any(kw in command for kw in ["open", "launch", "start"]):
            target = command.replace("open ", "").replace("launch ", "").replace("start ", "").strip()
            return self._open_app(target)

        # 3. App Closing (Improved with psutil)
        if any(kw in command for kw in ["close", "stop running", "terminate"]):
            target = command.replace("close ", "").replace("stop running ", "").replace("terminate ", "").strip()
            if not target:
                self.context = 'close_app'
                return "Which application should I close?"
            return self._close_app(target)

        # 4. System Toggles (WiFi/BT)
        if "wifi" in command or "wi-fi" in command or "internet" in command:
            if any(kw in command for kw in ["on", "enable", "connect"]): return self._toggle_wifi(True)
            if any(kw in command for kw in ["off", "disable", "disconnect"]): return self._toggle_wifi(False)
        
        if "bluetooth" in command:
            if any(kw in command for kw in ["on", "enable"]): return self._toggle_bluetooth(True)
            if any(kw in command for kw in ["off", "disable"]): return self._toggle_bluetooth(False)

        # 5. Vol/Bright
        if "volume" in command or "sound" in command:
            if self._handle_relative_volume(command): return "Sound level adjusted."
            nums = re.findall(r'\d+', command)
            if nums:
                self.set_volume(int(nums[0]))
                return f"Volume set to {nums[0]} percent."
            self.context = 'volume'
            return "What volume level would you like?"

        if "brightness" in command:
            if self._handle_relative_brightness(command): return "Brightness adjusted."
            nums = re.findall(r'\d+', command)
            if nums:
                self.set_brightness(int(nums[0]))
                return f"Brightness set to {nums[0]} percent."
            return "How bright should I set it?"

        # 6. Mute/Lock/Airplane/Focus
        if "airplane mode" in command:
            if "on" in command or "enable" in command: return self._set_airplane_mode(True)
            if "off" in command or "disable" in command: return self._set_airplane_mode(False)
        
        if "focus mode" in command:
            if "on" in command or "enable" in command: return self._set_focus_mode(True)
            if "off" in command or "disable" in command: return self._set_focus_mode(False)

        if "mute" in command: return self._mute_audio(True)
        if "unmute" in command: return self._mute_audio(False)
        if "lock" in command and ("screen" in command or "computer" in command): return self._lock_screen()

        # 7. Explicit Search
        if any(kw in command for kw in ["search google for", "google search for"]):
            query = re.sub(r'search google for |google search for ', '', command).strip()
            return self._web_search(query)

        # 8. Chat
        if any(kw in command for kw in ["hello", "hi computer", "hey computer"]):
            return "Hello! I'm ready for your commands."
        
        if "who are you" in command:
            return "I'm Computer, your AI assistant optimized for Windows."

        print(f"[Warning] Unknown command pattern: {command}. Defaulting to Ollama")
        if self.advanced_mode and self.ollama and self.ollama.is_available:
            return self.ollama.query(command)
        
        search_res = self._web_search(command)
        return search_res

    def _open_app(self, target: str) -> str:
        target = target.lower().strip()
        # Explicit system overrides
        overrides = {
            "control panel": "control",
            "settings": "start ms-settings:",
            "task manager": "taskmgr",
            "notepad": "notepad",
            "calculator": "calc",
            "chrome": "start chrome",
            "edge": "start msedge",
            "cmd": "start cmd",
            "terminal": "start wt || start cmd"
        }
        
        if target in overrides:
            subprocess.run(overrides[target], shell=True)
            return f"Opening {target}."

        # Search cache
        if target in self.app_cache:
            os.startfile(self.app_cache[target])
            return f"Opening {target}."
        
        # Substring fuzzy
        for name, path in self.app_cache.items():
            if target in name:
                os.startfile(path)
                return f"Opening {name}."
        
        # Web fallback
        webbrowser.open(f"https://www.google.com/search?q={target}")
        return f"I couldn't find {target} locally, searching online instead."

    def _close_app(self, app_name: str) -> str:
        app_name = app_name.lower().strip()
        print(f"[System] Attempting to close app: {app_name}")
        
        # Immediate kills for tricky Windows targets
        if "setting" in app_name:
            subprocess.run("taskkill /F /IM SystemSettings.exe", shell=True, capture_output=True)
            return "Closed Settings."
        if "control" in app_name or "panel" in app_name:
            subprocess.run("taskkill /F /IM control.exe", shell=True, capture_output=True)
            return "Closed Control Panel."

        if psutil:
            closed_count = 0
            for proc in psutil.process_iter(['name', 'exe']):
                try:
                    pname = (proc.info['name'] or "").lower()
                    pexe = (proc.info['exe'] or "").lower()
                    parent_name = ""
                    try: parent_name = proc.parent().name().lower()
                    except: pass
                    
                    if app_name in pname or (pexe and app_name in pexe) or (parent_name and app_name in parent_name):
                        proc.kill()
                        closed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if closed_count > 0:
                print(f"[System] Closed {closed_count} instances of {app_name}")
                return f"Closed {app_name}."

        # Fallback to a broader PowerShell search/kill
        ps_cmd = f'Get-Process | Where-Object {{ $_.ProcessName -like "*{app_name}*" -or $_.MainWindowTitle -like "*{app_name}*" }} | Stop-Process -Force -ErrorAction SilentlyContinue'
        try:
            subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
            return f"Closing processes matching '{app_name}'."
        except:
            return f"Failed to close {app_name}."

    def _scheduler_loop(self):
        """Background thread to handle alarms, timers, and reminders."""
        import winotify
        # Lazy load pygame for sound
        try:
            import pygame
            pygame.mixer.init()
        except: pygame = None

        while not self.should_exit:
            try:
                now = datetime.datetime.now()
                
                # Check Alarms & Timers
                for alarm in self.alarms[:]:
                    try:
                        target_time = datetime.datetime.fromisoformat(alarm["time"])
                        if now >= target_time:
                            print(f"[Trigger] Alarm/Timer: {alarm['label']}")
                            
                            # Play sound
                            if pygame:
                                try:
                                    # Fallback to Alarm01.wav
                                    pygame.mixer.music.load(r"C:\Windows\Media\Alarm01.wav")
                                    pygame.mixer.music.play()
                                except: pass
                            
                            try:
                                toast = winotify.Notification(app_id="Computer Agent", title="ALARM/TIMER", msg=alarm['label'])
                                toast.show()
                            except: pass
                            self.alarms.remove(alarm)
                            self._save_data()
                    except Exception as e:
                        print(f"[Alarm Error] {e}")
                
                # Check Reminders
                for rem in self.reminders[:]:
                    try:
                        target_time = datetime.datetime.fromisoformat(rem["time"])
                        if now >= target_time:
                            print(f"[Trigger] Reminder: {rem['text']}")
                            
                            if pygame:
                                try:
                                    pygame.mixer.music.load(r"C:\Windows\Media\Windows Notify System Generic.wav")
                                    pygame.mixer.music.play()
                                except: pass
                                
                            try:
                                toast = winotify.Notification(app_id="Computer Agent", title="REMINDER", msg=rem['text'])
                                toast.show()
                            except: pass
                            self.reminders.remove(rem)
                            self._save_data()
                    except Exception as e:
                        print(f"[Reminder Error] {e}")
            except Exception as e:
                print(f"[Scheduler Loop Error] {e}")
            
            time.sleep(1)

    def _set_alarm(self, command: str) -> str:
        # Improved extraction
        match = re.search(r'(\d{1,2})[:.]?(\d{0,2})?\s*(am|pm)?', command)
        if not match: return "What time should I set the alarm for? (e.g., 'alarm at 7:30 PM')"
        
        try:
            hr = int(match.group(1))
            mn = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3).lower() if match.group(3) else None
            
            if ampm == 'pm' and hr < 12: hr += 12
            if ampm == 'am' and hr == 12: hr = 0
                
            now = datetime.datetime.now()
            target = now.replace(hour=hr, minute=mn, second=0, microsecond=0)
            if target <= now:
                target += datetime.timedelta(days=1)
                
            label = command.replace("set an alarm", "").replace("alarm", "").replace("for", "").replace("at", "").replace(match.group(0), "").strip() or "Alarm"
            self.alarms.append({"time": target.isoformat(), "label": label})
            self._save_data()
            return f"Ok, alarm set for {target.strftime('%I:%M %p')}."
        except Exception as e:
            return f"Sorry, I couldn't set that alarm: {str(e)}"

    def _clear_alarms(self) -> str:
        self.alarms = []
        self._save_data()
        return "All alarms and timers cleared."

    def _set_timer(self, command: str) -> str:
        # timer for 10 minutes
        match = re.search(r'(\d+)\s*(minute|second|hour|hour|min|sec)', command)
        if not match: return "How long should I set the timer for? (e.g. 'timer for 5 minutes')"
        
        try:
            val = int(match.group(1))
            unit = match.group(2).lower()
            
            delta = datetime.timedelta(minutes=val)
            if 'sec' in unit: delta = datetime.timedelta(seconds=val)
            elif 'hour' in unit: delta = datetime.timedelta(hours=val)
            
            target = datetime.datetime.now() + delta
            label = f"Timer for {val} {unit} finished."
            self.alarms.append({"time": target.isoformat(), "label": label})
            self._save_data()
            return f"Timer started for {val} {unit}."
        except Exception as e:
            return f"Failed to start timer: {str(e)}"

    def _add_reminder(self, command: str) -> str:
        # remind me to take out the trash at 8 PM
        try:
            parts = command.split("remind me to")
            if len(parts) < 2: return "Try: 'remind me to [task] at [time]'"
            
            task_part = parts[1].split("at")[0].strip()
            time_part = parts[1].split("at")[-1].strip()
            
            match = re.search(r'(\d{1,2})[:.]?(\d{0,2})?\s*(am|pm)?', time_part)
            if not match: return "What time should I remind you?"
            
            hr = int(match.group(1))
            mn = int(match.group(2)) if match.group(2) else 0
            ampm = match.group(3).lower() if match.group(3) else None
            
            if ampm == 'pm' and hr < 12: hr += 12
            if ampm == 'am' and hr == 12: hr = 0
            
            now = datetime.datetime.now()
            target = now.replace(hour=hr, minute=mn, second=0, microsecond=0)
            if target <= now: target += datetime.timedelta(days=1)
            
            self.reminders.append({"time": target.isoformat(), "text": task_part})
            self._save_data()
            return f"I'll remind you to {task_part} at {target.strftime('%I:%M %p')}."
        except:
            return "Try saying 'remind me to [task] at [time]'."

    def _create_note(self, command: str) -> str:
        # 1. Folder Setup
        notes_dir = os.path.join(os.getcwd(), "notes")
        if not os.path.exists(notes_dir): os.makedirs(notes_dir)
        
        # 2. Extract content
        content = ""
        if "that says" in command:
            content = command.split("that says")[-1].strip()
        elif "note" in command:
            content = command.replace("create a note", "").replace("take a note", "").replace("note", "").strip()
        
        if not content: return "What should I write in the note?"
        
        # 3. Save as .txt
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"note_{timestamp}.txt"
        filepath = os.path.join(notes_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Note Taken: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 20 + "\n")
                f.write(content)
            
            # 4. Open with Notepad
            os.startfile(filepath)
            
            # Keep log in data file too
            self.notes.append({"date": datetime.datetime.now().isoformat(), "content": content, "file": filepath})
            self._save_data()
            
            return f"Note saved to {filename} and opened in Notepad."
        except Exception as e:
            return f"Failed to save physical note: {e}"

    def _read_notes(self) -> str:
        if not self.notes: return "You have no notes."
        res = "Your recent notes: "
        for i, note in enumerate(self.notes[-3:]):
             res += f"{i+1}. {note['content']}. "
        return res

    def _add_to_list(self, command: str) -> str:
        try:
            item = command.split("add")[-1].split("to")[0].strip()
            list_name = command.split("my")[-1].replace("list", "").strip() or "grocery"
            
            if list_name not in self.lists: self.lists[list_name] = []
            self.lists[list_name].append(item)
            self._save_data()
            return f"Added {item} to your {list_name} list."
        except:
            return "Try saying 'add [item] to my [list name] list'."

    def _read_list(self, command: str) -> str:
        list_name = command.replace("read my", "").replace("show my", "").replace("list", "").strip() or "grocery"
        if list_name not in self.lists or not self.lists[list_name]:
            return f"Your {list_name} list is empty."
        return f"Items in {list_name}: {', '.join(self.lists[list_name])}."

    def _take_screenshot(self) -> str:
        try:
            import mss
            filename = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            with mss.mss() as sct:
                sct.shot(output=filename)
            return f"Screenshot saved as {filename}."
        except Exception as e:
            return f"Failed to take screenshot: {e}"

    def _calculate(self, command: str) -> str:
        try:
            if "tip" in command:
                nums = re.findall(r'(\d+(?:\.\d+)?)', command)
                if len(nums) >= 2:
                    percent = float(nums[0])
                    amount = float(nums[1])
                    tip = (percent / 100) * amount
                    return f"A {percent}% tip on ${amount:.2f} is ${tip:.2f}. Total is ${(amount+tip):.2f}."

            clean_cmd = command.replace("what is", "").replace("calculate", "").replace("x", "*").replace("times", "*").replace("divided by", "/").replace("plus", "+").replace("minus", "-")
            expr = "".join(c for c in clean_cmd if c in "0123456789.+-*/ ")
            if expr.strip():
                result = eval(expr)
                return f"The result is {result}."
        except: pass
        return "I couldn't calculate that."

    def _play_music(self, command: str) -> str:
        query = command.replace("play", "").replace("music", "").strip()
        webbrowser.open(f"https://www.youtube.com/results?search_query={query}")
        return f"Playing {query} on YouTube."

    def _identify_song(self) -> str:
        webbrowser.open("https://www.google.com/search?q=what+song+is+this")
        return "Opening Google to identify the song."

    def _get_weather(self, command: str) -> str:
        query = command.replace("what's", "").replace("what is", "").strip() or "weather today"
        return self._web_search(query)

    def _get_sports(self, command: str) -> str:
        query = command.replace("get", "").replace("check", "").strip()
        return self._web_search(query)

    def _check_calendar(self) -> str:
        webbrowser.open("https://calendar.google.com")
        return "Opening your calendar."

    def _check_emails(self) -> str:
        webbrowser.open("https://mail.google.com")
        return "Opening your emails."

    def _get_directions(self, command: str) -> str:
        dest = command.replace("directions to", "").replace("give me", "").strip()
        webbrowser.open(f"https://www.google.com/maps/dir/?api=1&destination={dest}")
        return f"Getting directions to {dest}."

    def _get_traffic(self, command: str) -> str:
        webbrowser.open("https://www.google.com/maps/@?api=1&map_action=map&layer=traffic")
        return "Showing current traffic."

    def _find_places(self, command: str) -> str:
        query = command.replace("find", "").replace("find a", "").strip()
        webbrowser.open(f"https://www.google.com/maps/search/{query}")
        return f"Finding {query} near you."

    def _check_flight(self, command: str) -> str:
        query = command.replace("check flight status of", "").replace("flight status", "").strip()
        return self._web_search(f"flight status {query}")

    def _lock_screen(self):
        import ctypes
        ctypes.windll.user32.LockWorkStation()
        return "Computer locked."

    def _get_battery_status(self) -> str:
        if not psutil: return "I need the psutil library to check battery."
        battery = psutil.sensors_battery()
        if battery is None:
            return "I couldn't detect a battery on this device."
        
        percent = battery.percent
        seconds = battery.secsleft
        plugged = battery.power_plugged
        
        status = "Charging" if plugged else "Not charging"
        res = f"Battery is at {percent} percent. {status}."
        
        if not plugged and seconds != psutil.POWER_TIME_UNLIMITED:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            res += f" You have about {hours} hours and {mins} minutes remaining."
        return res

    def _get_system_info(self) -> str:
        if not psutil: return "I need the psutil library for system info."
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        return f"CPU usage is at {cpu} percent. Memory usage is at {mem.percent} percent."

    def _toggle_wifi(self, enable: bool) -> str:
        s = "enabled" if enable else "disabled"
        res1 = subprocess.run(f'netsh interface set interface "WiFi" {s}', shell=True, capture_output=True, text=True)
        res2 = subprocess.run(f'netsh interface set interface "Wi-Fi" {s}', shell=True, capture_output=True, text=True)
        if "requires" in res1.stderr.lower() or "privileges" in res1.stderr.lower():
            return "I need Administrator rights for WiFi toggles."
        if res1.returncode == 0 or res2.returncode == 0:
            return f"WiFi {s}."
        return "Failed to toggle WiFi."

    def _toggle_bluetooth(self, enable: bool) -> str:
        act = "Enable-PnpDevice" if enable else "Disable-PnpDevice"
        ps = f'Get-PnpDevice | Where-Object {{$_.Class -eq "Bluetooth"}} | {act} -Confirm:$false'
        res = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True, shell=True)
        if "requires" in res.stderr.lower() or "privileges" in res.stderr.lower() or "AccessDenied" in res.stderr:
            return "I need Administrator rights for Bluetooth toggles."
        return f"Bluetooth toggle {'successful' if res.returncode == 0 else 'failed'}."

    def _mute_audio(self, mute: bool):
        if self._init_volume_interface():
            try:
                self._volume_interface.SetMute(1 if mute else 0, None)
                return "Muted." if mute else "Unmuted."
            except: pass
        return "Audio control failed."

    def set_volume(self, level):
        level = max(0, min(100, level))
        if self._init_volume_interface():
            try:
                self._volume_interface.SetMasterVolumeLevelScalar(level / 100.0, None)
                self.current_volume = level
                print(f"[System] Volume set to {level}%")
            except: pass

    def _get_current_volume(self) -> int:
        if not self._init_volume_interface(): return 50
        try:
            val = int(self._volume_interface.GetMasterVolumeLevelScalar() * 100)
            self.current_volume = val
            return val
        except: return 50

    def _handle_relative_volume(self, command):
        curr = self._get_current_volume()
        step = 15
        if any(kw in command for kw in ["up", "louder", "increase", "higher"]):
            self.set_volume(curr + step)
            return True
        if any(kw in command for kw in ["down", "quieter", "decrease", "lower"]):
            self.set_volume(curr - step)
            return True
        return False

    def set_brightness(self, level):
        try:
            import screen_brightness_control as sbc
            sbc.set_brightness(max(0, min(100, level)))
            self.current_brightness = level
        except: pass

    def _handle_relative_brightness(self, command):
        step = 20
        if any(kw in command for kw in ["up", "brighter", "increase"]):
            self.set_brightness(self.current_brightness + step)
            return True
        if any(kw in command for kw in ["down", "dimmer", "decrease"]):
            self.set_brightness(self.current_brightness - step)
            return True
        return False

    def _web_search(self, query: str) -> str:
        webbrowser.open(f"https://www.google.com/search?q={query}")
        try:
            if hasattr(self, 'ollama') and self.ollama and self.ollama.is_available:
                ans = self.ollama.query(f"Briefly answer the search query: {query}", use_context=False)
                return f"I opened Google for you. Here is the answer: {ans}"
        except Exception as e:
            print(f"[Ollama fallback exception]: {e}")
            pass
            
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                pass
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=1))
                if results:
                    return f"This is what I found: {results[0]['body']}"
        except Exception as e:
            print(f"[Search exception]: {e}")
            pass
            
        return f"I am searching Google for {query}."

    def _activate_advanced_mode(self):
        try:
            from ollama_integration import OllamaIntegration
            self.ollama = OllamaIntegration()
            if self.ollama.is_available:
                self.advanced_mode = True
                return f"Advanced Mode is now ONLINE using {self.ollama.model}."
            return "Ollama Desktop is not running."
        except Exception as e:
            return f"Error: {str(e)}"

    def _deactivate_advanced_mode(self):
        self.advanced_mode = False
        self.ollama = None
        return "Advanced Mode disabled."

    def _activate_vision_mode(self):
        try:
            from vision_integration import VisionIntegration
            self.vision = VisionIntegration()
            if self.vision.activate():
                self.vision_mode = True
                return "Vision Mode is now ACTIVE."
            return "Vision failed to initialize."
        except: return "Vision initialization error."

    def _deactivate_vision_mode(self):
        if self.vision: self.vision.deactivate()
        self.vision_mode = False
        self.vision = None
        return "Vision Mode disabled."

    def _query_ollama(self, query):
        return self.ollama.query(query) if self.ollama else "Advanced mode is not ready."

    def _describe_screen(self):
        return self.vision.describe_screen() if self.vision else "Vision mode is not ready."

    def _find_object(self, obj):
        if not self.vision: return "Vision mode is not ready."
        found = self.vision.find_object(obj)
        return f"Yes, I see {obj}." if found else f"No, I don't see {obj}."

    # --- New OS Modes ---
    def _set_airplane_mode(self, enable: bool) -> str:
        s = "on" if enable else "off"
        print(f"[System] Toggling Airplane Mode: {s}")
        try:
            # 1. Toggle WiFi & BT (Most immediate effect)
            self._toggle_wifi(not enable)
            self._toggle_bluetooth(not enable)
            
            # 2. Registry attempt (Requires Admin)
            state = "1" if enable else "0"
            cmd = fr'reg add "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\RadioManagement\SystemRadioState" /v "ResourceMetadata" /t REG_DWORD /d {state} /f'
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if "access is denied" in res.stderr.lower():
                return f"WiFi and Bluetooth turned {s}, but I need Administrator rights to fully toggle the Airplane Mode switch."
            
            return f"Airplane mode is now {s}."
        except:
            return "Failed to fully toggle Airplane mode."

    def _set_focus_mode(self, enable: bool) -> str:
        s = "on" if enable else "off"
        print(f"[System] Toggling Focus Mode: {s}")
        try:
            # 1. NOC_GLOBAL_SETTING_TOASTS_ENABLED
            state = "1" if enable else "0"
            ps1 = f'Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings" -Name "NOC_GLOBAL_SETTING_TOASTS_ENABLED" -Value {state}'
            subprocess.run(["powershell", "-Command", ps1], capture_output=True)
            
            # 2. FocusAssistState (2 = Priority Only / DND, 0 = Off)
            ps2 = f'Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings" -Name "FocusAssistState" -Value {"2" if enable else "0"}'
            subprocess.run(["powershell", "-Command", ps2], capture_output=True)
            
            # 3. QuietHours (Supplemental for older Win10/11 builds)
            ps3 = f'Set-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings" -Name "QuietHoursState" -Value {state}'
            subprocess.run(["powershell", "-Command", ps3], capture_output=True)
            
            return f"Focus mode (Do Not Disturb) is now {s}."
        except Exception as e:
            return f"Failed to toggle focus mode: {e}"
