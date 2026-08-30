@echo off
cd /d "%~dp0"
call venv_chatterbox\Scripts\activate
start /b pythonw ChatterText_3.0.py > log.txt 2>&1