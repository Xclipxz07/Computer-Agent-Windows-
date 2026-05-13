@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo    Claire 2.0 - Automated Setup
echo ==========================================
echo.

:: 1. Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

:: 2. Create Virtual Environment
echo [1/4] Creating virtual environment (.venv)...
if not exist .venv (
    python -m venv .venv
) else (
    echo .venv already exists, skipping...
)

:: 3. Upgrade Pip
echo [2/4] Upgrading pip...
.venv\Scripts\python.exe -m pip install --upgrade pip

:: 4. Install Requirements
echo [3/4] Installing dependencies from requirements.txt...
if exist requirements.txt (
    .venv\Scripts\python.exe -m pip install -r requirements.txt
) else (
    echo [Warning] requirements.txt not found.
)

:: 5. Final Checks
echo [4/4] Finalizing setup...
echo.
echo ==========================================
echo    Setup Complete!
echo ==========================================
echo.
echo To run Claire, use: start_computer_agent.bat
echo or run: .venv\Scripts\python.exe main.py
echo.
pause
