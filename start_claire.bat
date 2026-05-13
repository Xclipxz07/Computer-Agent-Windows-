@echo off
setlocal
cd /d "%~dp0"
echo Starting Claire 2.0...
call .venv\Scripts\activate.bat
python main.py
pause
