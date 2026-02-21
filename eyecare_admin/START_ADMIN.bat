@echo off
echo ================================
echo   EyeCare Admin Dashboard
echo ================================
echo.
echo Starting Admin Dashboard on port 5001...
echo Open: http://localhost:5001
echo.

:: Change to the script's directory
cd /d "%~dp0"

:: Run with venv Python directly
.venv\Scripts\python.exe app.py

pause
