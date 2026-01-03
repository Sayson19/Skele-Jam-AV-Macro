@echo off
echo ================================
echo   ArbuzAV EXE Builder
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed!
    echo Please install Python from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Running build script...
echo.
python build_exe.py

echo.
echo ================================
echo Build process completed!
echo Check the 'dist' folder for ArbuzAV.exe
echo ================================
pause
