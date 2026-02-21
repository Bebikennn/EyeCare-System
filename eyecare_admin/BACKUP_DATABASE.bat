@echo off
REM Automated Database Backup Script for Windows Task Scheduler
REM Place this in the eyecare_admin folder and schedule it

cd /d "%~dp0"

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run backup script
python scripts\backup_database.py backup

REM Log the result
echo Backup completed at %date% %time% >> logs\backup.log

deactivate
