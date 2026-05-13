try:
    print("Testing imports...")
    import sys
    import os
    import PyQt6
    import pynput
    import speech_recognition
    import pygame
    import pycaw
    import comtypes
    import screen_brightness_control
    import fuzzywuzzy
    import Levenshtein
    import duckduckgo_search
    import pvporcupine
    import ollama
    import PIL
    import mss
    import requests
    import winotify
    import pywifi
    import psutil
    import edge_tts
    print("All imports successful!")
except ImportError as e:
    print(f"Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    sys.exit(1)
