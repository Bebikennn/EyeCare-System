@echo off
REM ============================================
REM EyeCare Backend - Development Server
REM ============================================

echo.
echo ============================================
echo   EyeCare Backend - Development Mode
echo ============================================
echo.

REM Check if virtual environment exists
if not exist ".venv\" (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv .venv
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install/upgrade dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Check if .env exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please copy .env.example to .env and configure your settings.
    echo.
    pause
    exit /b 1
)

REM Create logs directory if it doesn't exist
if not exist "logs\" mkdir logs

REM Start the development server
echo.
echo Starting development server...
echo.
python app.py

pause
