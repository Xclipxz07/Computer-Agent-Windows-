from assistant import Assistant
import time
import os

def test_features():
    print("--- Testing Computer Refined Features ---")
    asst = Assistant()
    
    # 1. Test Notepad Note
    print("\nTesting Notepad Note Creation...")
    res = asst.process_command("take a note that says Testing Notepad Integration")
    print(f"Result: {res}")
    
    # Check if folder and file exist
    notes_dir = os.path.join(os.getcwd(), "notes")
    if os.path.exists(notes_dir):
        files = os.listdir(notes_dir)
        print(f"Files in notes folder: {files}")
    else:
        print("Error: notes folder not found!")
    
    # 2. Test Alarm Sound logic (Simulated)
    print("\nTesting Timer Logic with New Sound (3 seconds)...")
    res = asst.process_command("set a timer for 3 seconds")
    print(f"Result: {res}")
    
    print("Waiting 5 seconds for trigger...")
    time.sleep(5)
    print("Check terminal for [Trigger] logs and if you heard a sound!")

    # 3. Test Focus Mode (DND)
    print("\nTesting Focus Mode Registry Toggle...")
    res = asst.process_command("activate focus mode")
    print(f"Result: {res}")

if __name__ == "__main__":
    test_features()
