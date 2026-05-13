from assistant import Assistant
import time

def test_new_flow():
    print("Initializing Assistant...")
    asst = Assistant()
    time.sleep(1)
    
    print("\n--- Test: Unknown Command triggers Google + Ollama Prompt ---")
    command = "what is the height of the burj khalifa"
    print(f"User: {command}")
    response = asst.process_command(command)
    print(f"Assistant: {response.encode('utf-8', errors='ignore').decode('utf-8')}")
    
    if "found on Google" in response or "searching Google" in response:
        if "Do you want me to work with Ollama?" in response:
            print("SUCCESS: AI searched Google and then asked about Ollama.")
        else:
            print("FAILURE: AI did not include the Ollama prompt.")
    else:
        print("FAILURE: AI did not trigger Google Search.")
        return

    print("\n--- Test: Affirmative Response (Yes) ---")
    command = "yes"
    print(f"User: {command}")
    response = asst.process_command(command)
    print(f"Assistant: {response.encode('utf-8', errors='ignore').decode('utf-8')}")
    if response and len(response) > 20: # Assumed Ollama response length
         print("SUCCESS: Assistant responded via Ollama.")
    else:
         print("FAILURE: No Ollama response.")

    print("\n--- Test: New Command then Negative Response (No) ---")
    command = "who won the world cup in 2022"
    asst.process_command(command)
    command = "no"
    print(f"User: {command}")
    response = asst.process_command(command)
    print(f"Assistant: {response}")
    if "opened" in response or "results" in response:
        print("SUCCESS: AI did nothing else on 'no'.")
    else:
        print("FAILURE: AI behavior on 'no' is incorrect.")

if __name__ == "__main__":
    test_new_flow()
