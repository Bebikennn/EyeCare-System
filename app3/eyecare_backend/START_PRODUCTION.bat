@echo off
REM ============================================
REM EyeCare Backend - Production Server
REM ============================================

echo.
echo ============================================
echo   EyeCare Backend - Production Mode
echo ============================================
echo.

REM Check if virtual environment exists
if not exist ".venv\" (
    echo Error: Virtual environment not found!
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo.
    echo ERROR: .env file not found!
    echo Production mode requires proper configuration.
    echo.
    pause
    exit /b 1
)

REM Create logs directory
if not exist "logs\" mkdir logs

REM Verify DEBUG is set to False
findstr /C:"DEBUG=True" .env >nul
if %errorlevel% == 0 (
    echo.
    echo WARNING: DEBUG mode is enabled in .env!
    echo This is NOT recommended for production.
    echo Press Ctrl+C to cancel or any key to continue...
    pause >nul
)

REM Start Gunicorn
echo.
echo Starting production server with Gunicorn...
echo.
gunicorn -c gunicorn_config.py app:app

pause
