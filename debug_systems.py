import ollama
import psutil
import json

def test_ollama():
    print("--- Testing Ollama ---")
    try:
        models = ollama.list()
        print(f"Ollama list response: {json.dumps(models, indent=2)}")
    except Exception as e:
        print(f"Ollama list error: {e}")

def test_psutil_close(target):
    print(f"--- Testing psutil close for: {target} ---")
    found = False
    for proc in psutil.process_iter(['name', 'username']):
        try:
            if target.lower() in proc.info['name'].lower():
                print(f"Found process: {proc.info['name']} (PID: {proc.pid})")
                found = True
        except: continue
    if not found:
        print(f"No process matching '{target}' found.")

if __name__ == "__main__":
    test_ollama()
    # Test with a common app like 'chrome' or 'notepad' if the user were running it
    test_psutil_close("chrome")
    test_psutil_close("notepad")
    test_psutil_close("settings")
