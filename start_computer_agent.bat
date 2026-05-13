@echo off
setlocal
cd /d "%~dp0"
echo Starting Computer Agent...
call .venv\Scripts\activate.bat
python main.py
pause
