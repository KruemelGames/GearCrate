@echo off
:: InvDetect - Star Citizen Universal Inventory Scanner
title InvDetect - Star Citizen Scanner vFinal
cd /d "%~dp0"

:: Check if running as admin
net session >nul 2>&1
if %errorlevel% == 0 (
    echo.
    echo   Administrator mode active - Starting scanner...
    echo.
    python main.py
) else (
    echo.
    echo   Starting as Administrator...
    echo.
    powershell -Command "Start-Process '%~dp0Start_scanner.bat' -Verb RunAs"
    exit
)

:: Optional: pause at the end if you want to see the output
:: Remove the next line if you want the window to close automatically after scan
pause