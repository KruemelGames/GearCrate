@echo off
REM ====================================
REM GearCrate - Desktop Mode (ADMIN)
REM ====================================
REM This script requests administrator privileges
REM Required for InvDetect scanner functionality

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    REM Already running as admin, start GearCrate
    goto :run_gearcrate
) else (
    REM Not admin, request elevation
    echo Requesting administrator privileges...
    echo.
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:run_gearcrate
REM Change to the directory where this batch file is located
cd /d "%~dp0"

echo ====================================
echo GearCrate - Desktop Mode (ADMIN)
echo ====================================
echo.
echo This mode starts GearCrate as
echo desktop application with admin rights.
echo.
echo Features:
echo - HTTP server in background
echo - Desktop window
echo - InvDetect Scanner with full privileges
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo.
    echo Please run setup.bat first to install all requirements.
    echo.
    pause
    exit /b 1
)

echo Starting GearCrate Desktop (Admin)...
echo Working Directory: %CD%
echo.

REM Start the desktop version
python src/main_desktop.py

if errorlevel 1 (
    echo.
    echo ====================================
    echo ERROR during startup!
    echo ====================================
    echo.
    echo Possible causes:
    echo - pywebview not installed
    echo - Port 8080 already in use
    echo.
    echo Try running setup.bat again to fix missing dependencies.
    echo.
    pause
)
