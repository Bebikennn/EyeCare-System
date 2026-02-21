@echo off
REM Run test suite with coverage

cd /d "%~dp0"

REM Activate virtual environment
call .venv\Scripts\activate.bat

echo Running test suite with coverage...
echo.

REM Run pytest with coverage
pytest

echo.
echo Test results saved to htmlcov/index.html
echo Open htmlcov/index.html in a browser to view detailed coverage report

deactivate
pause
