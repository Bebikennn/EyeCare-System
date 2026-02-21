@echo off
REM Run code quality checks

cd /d "%~dp0"

REM Activate virtual environment
call .venv\Scripts\activate.bat

echo ========================================
echo Running Code Quality Checks
echo ========================================
echo.

echo [1/4] Running Black (Code Formatter)...
black --check . --exclude="/(\.venv|venv|migrations|trashbin|build|htmlcov)/"
echo.

echo [2/4] Running isort (Import Sorter)...
isort --check-only . --skip .venv --skip venv --skip migrations --skip trashbin
echo.

echo [3/4] Running Flake8 (Style Guide)...
flake8 .
echo.

echo [4/4] Running Pylint (Code Analysis)...
pylint app.py database.py config.py --rcfile=.pylintrc
pylint routes/ --rcfile=.pylintrc
pylint utils/ --rcfile=.pylintrc 2>nul
echo.

echo ========================================
echo Code Quality Check Complete!
echo ========================================
echo.
echo To auto-fix formatting issues, run:
echo   black .
echo   isort .

deactivate
pause
