from assistant import Assistant
import time

def test_final():
    print("Initializing Assistant for final test...")
    asst = Assistant()
    
    test_cases = [
        "ask agent what is the weather",
        "ask ag what is the weather",
        "aska agent tell me a joke",
        "osga agent who are you",
        "claire tell me a story"
    ]
    
    for cmd in test_cases:
        print(f"\nTesting: '{cmd}'")
        # We mock Ollama availability to True for testing routing
        if not asst.advanced_mode:
            asst.advanced_mode = True
            from unittest.mock import MagicMock
            asst.ollama = MagicMock()
            asst.ollama.query.return_value = "Ollama response received."
        
        response = asst.process_command(cmd)
        print(f"Response: {response}")
        if "Ollama response received" in response or "Detected and using" in response:
             print("Result: SUCCESS (Routed to Ollama)")
        else:
             print("Result: FAILURE")

if __name__ == "__main__":
    test_final()
