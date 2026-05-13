from assistant import Assistant
import time

def test_assistant():
    print("Initializing Assistant...")
    asst = Assistant()
    # Wait for app cache thread to start if needed, but not necessary for this test
    time.sleep(1) 
    
    print("\nTest 1: Normal command")
    print(f"Response: {asst.process_command('what time is it')}")
    
    print("\nTest 2: Ask agent command")
    response = asst.process_command("ask agent what is the capital of France")
    print(f"Response: {response}")
    
    if "Advanced mode is not available" in response or "Ollama Desktop is not running" in response:
        print("\nFAILURE: Ollama not working in Assistant.")
    elif "Error" in response:
         print(f"\nFAILURE: Error occurred: {response}")
    else:
        print("\nSUCCESS: Assistant responded via Ollama (presumably).")

if __name__ == "__main__":
    test_assistant()
