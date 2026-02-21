@echo off
echo ================================
echo   EyeCare Backend Server
echo ================================
echo.

REM Check if virtual environment exists
if exist ".venv\Scripts\python.exe" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo No virtual environment found, using system Python...
)

echo Starting Flask backend on port 5000...
echo.

cd eyecare_backend
python app.py

pause
