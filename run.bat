@echo off
echo ================================
echo      ArbuzAV Launcher
echo ================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed!
    echo Please install Python from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Install requirements if needed
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing/Updating requirements...
pip install -r requirements.txt --quiet
echo.

echo Starting ArbuzAV...
echo.
python ArbuzAV.py

pause
