@echo off
REM ============================================
REM EyeCare Backend - Run Tests
REM ============================================

echo.
echo ============================================
echo   EyeCare Backend - Test Suite
echo ============================================
echo.

REM Activate virtual environment
if exist ".venv\" (
    call .venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found, using system Python
)

REM Install test dependencies
pip install pytest pytest-cov --quiet

REM Run tests
echo.
echo Running tests...
echo.
pytest tests/ -v --cov=. --cov-report=html --cov-report=term

echo.
echo ============================================
echo   Test Results
echo ============================================
echo   HTML Report: htmlcov\index.html
echo ============================================
echo.

pause
