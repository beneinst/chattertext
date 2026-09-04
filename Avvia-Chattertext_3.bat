@echo off
cd /d "%~dp0"
start "" /b "%~dp0venv_chatterbox\Scripts\pythonw.exe" "%~dp0ChatterText_3.0.py"
exit /b
