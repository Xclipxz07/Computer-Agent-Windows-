# Computer Agent - The Siri/Cortana Replacement for Windows
<img width="1920" height="1200" alt="Screenshot (13)" src="https://github.com/user-attachments/assets/ca660fbf-bb48-4344-b96b-7f71e658ce02" />

Computer Agent is a high-performance, voice-activated AI assistant for Windows, designed to be a private and customizable replacement for Siri or Cortana. It is powered by **Ollama**, allowing you to run powerful LLMs locally on your machine for maximum privacy and speed.

## 🚀 Key Features

*   **Local AI Power:** Integrated with **Ollama**. Choose any model (Llama3, Phi3, Mistral, SmolLM, etc.) to drive your assistant's intelligence.
*   **System Control:** Control your PC using just your voice:
    *   Change volume and brightness.
    *   Toggle Wi-Fi and Bluetooth.
    *   Open and close applications.
    *   Lock your screen.
*   **Productivity Tools:** 
    *   Set alarms, timers, and reminders.
    *   Take notes and create grocery lists.
    *   Take screenshots instantly.
    *   Perform calculations and web searches.
*   **Advanced Voice Engine:** Optimized for distance and sensitivity, allowing you to trigger the agent with the wake word **"Computer"** from across the room.
*   **Privacy First:** Everything runs locally on your machine. No voice data or queries are sent to the cloud (except for explicit Google searches).

## 🛠️ How It Works
<img width="1920" height="1200" alt="Screenshot (14)" src="https://github.com/user-attachments/assets/a3769da5-d3fe-403f-95fc-0301bda638eb" />

1.  **Wake Word Detection:** The agent listens for "Computer" or "Claire" using a highly sensitive background listener.
2.  **Siri-Style UI:** Upon activation, a sleek, translucent overlay appears on your screen, indicating that it's listening.
3.  **Intelligent Routing:**
    *   **System Commands:** If you ask to "open Chrome" or "set volume to 50", the agent executes the system command directly.
    *   **Advanced Reasoning:** For complex questions or general chat, the agent routes the query to your local **Ollama** model.
    *   **Web Search:** If the query requires real-time info, it can perform a Google search and present the results.

## ⚙️ Configuration (Ollama Models)

You can easily change which local model the agent uses. See the [README.md](./README.md) file for detailed instructions on model selection and priority.

## 📦 Installation

1.  **Prerequisites:** 
    *   Install [Ollama](https://ollama.com/).
    *   Install Python 3.10+.
2.  **Setup:**
    *   Clone this repository.
    *   Run `setup_agent.bat` to install all dependencies.
3.  **Run:**
    *   Start the assistant using `start_computer_agent.bat`.

## ⌨️ Shortcuts
*   **Wake Word:** "Computer" or "Claire"
*   **Manual Trigger:** `Ctrl + Shift + C`
*   **Stop/End Conversation:** "Stop", "Goodbye", or "That's all"

---
*Created by Prabhat ##Apex Innovation*


# Computer Agent - Ollama Configuration Guide

This document explains how to manage and change the local AI model used by the Computer Agent.

## 1. Where the Model is Defined
All Ollama-related logic is located in `ollama_integration.py`. The agent uses the `OllamaIntegration` class to handle communication with your local Ollama server.

## 2. Automatic Model Selection
By default, the agent is designed to be "plug-and-play." When it starts, it performs the following steps:
1. It connects to your local Ollama instance.
2. It retrieves a list of all models you have downloaded (`ollama list`).
3. It searches for the best available model based on a **priority list** optimized for speed.

### The Priority List
Located on **line 41** of `ollama_integration.py`:
```python
priority = ['smollm', 'phi3', 'tinydolphin', 'orca-mini', 'llama3', 'mistral']
```
The agent will use the first model from this list that it finds on your system.

## 3. How to Change the Model

### Option A: Change the Preference Order
If you want the agent to prefer a different model (e.g., `llama3` over `phi3`), move your preferred model to the front of the `priority` list in `ollama_integration.py`.

### Option B: Force a Specific Model
To bypass the auto-detection and force the agent to use one specific model, modify the `_check_availability` method:

1. Open `ollama_integration.py`.
2. Locate the `_check_availability` method.
3. Replace the loop logic with a direct assignment:

```python
def _check_availability(self) -> bool:
    try:
        # ... existing connection code ...
        self.model = "your-model-name-here" # e.g., "llama3:8b"
        self.is_available = True
        return True
    except Exception as e:
        # ... error handling ...
```

## 4. Troubleshooting
*   **Model not found:** Ensure you have pulled the model using the command line: `ollama pull <model_name>`.
*   **Connection Error:** Make sure the Ollama application is running in your system tray or as a service.
*   **Slow Responses:** Larger models (like Llama3 or Mistral) may take longer to respond than lightweight models like `smollm` or `phi3`.
