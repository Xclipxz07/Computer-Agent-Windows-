# Claire 2.0 - Universal Setup Guide

Follow these steps to set up and run Claire 2.0 on any Windows computer.

## 1. Prerequisites

Before installing Claire, ensure you have the following installed on your system:

- **Python 3.10 or higher**: [Download from Python.org](https://www.python.org/downloads/) (Make sure to check "Add Python to PATH" during installation).
- **Ollama**: [Download from Ollama.com](https://ollama.com/download) (Required for advanced reasoning capabilities).
    - After installing, run `ollama pull smollm2:1.7b-instruct-q8_0` in your terminal to download the default model.
- **Windows 11 (22H2+)**: Recommended for the best experience with **Voice Access**.

## 2. Automated Installation

We've provided a one-click setup script to handle the technical details.

1.  Open the `Claire 2.0` project folder.
2.  Double-click on **`setup_agent.bat`**.
3.  The script will:
    - Create a local virtual environment (`.venv`).
    - Upgrade `pip`.
    - Install all required Python libraries (PyQt6, SpeechRecognition, etc.).
    - Verify your environment.

## 3. Running the Agent

Once the setup is complete, you can start Claire anytime by:

- Double-clicking **`start_claire.bat`**.

## 4. (Optional) Enable Voice Access

For near-instant voice detection, enable Windows Voice Access:

1.  Go to **Settings > Accessibility > Speech**.
2.  Toggle **Voice access** to **On**.
3.  Claire will automatically hook into Voice Access whenever she is listening!

---

## Troubleshooting

- **Microphone not detected**: Ensure your microphone is correctly plugged in and Windows Privacy settings allow apps to access the microphone.
- **Ollama Error**: Ensure the Ollama app is running in your system tray before starting Claire.
- **Missing DLLs**: If you see errors about missing DLLs, you may need to install the [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe).




Setup_agent.bat file is the new updated file install that please
