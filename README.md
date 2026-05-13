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
