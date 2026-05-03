@echo off
setlocal

REM Vai nella cartella dell'app
cd /d "C:\ChatterText\chattertext"

REM Avvia l'app usando l'ambiente chatterbox
"C:\Intel\Miniforge3\condabin\mamba.bat" run -n chatterbox pythonw ChatterText-App-23.py

endlocal