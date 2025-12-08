@echo off
:: ====================================
:: AUTO-ADMIN CHECK
:: ====================================
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"

if %errorlevel% neq 0 (
    echo Fordere Administrator-Rechte an...
    echo.
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: ====================================
:: AB HIER LAUFT ES ALS ADMIN
:: ====================================

setlocal EnableDelayedExpansion
title GearCrate Setup - 2025 Edition

:: LOG-DATEI INITIALISIEREN
set "LOGFILE=%~dp0setup-log.txt"
echo ========================================= > "%LOGFILE%"
echo GearCrate Setup Log >> "%LOGFILE%"
echo Started: %date% %time% >> "%LOGFILE%"
echo ========================================= >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo =========================================
echo       GearCrate - Installation Setup
echo =========================================
echo.
echo Log-Datei: setup-log.txt
echo.
echo =========================================
echo.

echo [LOG] Setup started as Administrator >> "%LOGFILE%"

:: ---------------------------------------------------
:: 1. Check if Python exists
:: ---------------------------------------------------
echo [1/3] Checking Python installation...
echo [1/3] Checking Python... >> "%LOGFILE%"

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python not found.
    echo [ERROR] Python not found >> "%LOGFILE%"
    goto :ASK_INSTALL_PYTHON
)

:: Get Python version using temp file to avoid escaping issues
python --version > "%TEMP%\pyver.txt" 2>&1
set /p PYTHON_VERSION_LINE=<"%TEMP%\pyver.txt"
del "%TEMP%\pyver.txt" 2>nul

:: Extract version number (e.g., "Python 3.11.9" -> "3.11.9")
for /f "tokens=2" %%a in ("%PYTHON_VERSION_LINE%") do set "PYTHON_VERSION=%%a"

echo [OK] Python !PYTHON_VERSION! found!
echo [OK] Python !PYTHON_VERSION! found >> "%LOGFILE%"

:: Extract major and minor version (e.g., "3.11.9" -> major=3, minor=11)
for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)

:: Warn if Python 3.13+
if !PY_MAJOR! GEQ 3 if !PY_MINOR! GEQ 13 (
    echo.
    echo [WARNING] Python !PYTHON_VERSION! detected!
    echo [WARNING] Python !PYTHON_VERSION! may have compatibility issues >> "%LOGFILE%"
    echo.
    echo Python 3.13+ may have compatibility issues with some packages.
    echo Recommended: Python 3.11 or 3.12
    echo.
    echo Do you want to continue anyway?
    choice /c YN /n /m " [Y] Yes, continue    [N] No, let me install Python 3.11/3.12 "
    if errorlevel 2 goto :MANUAL_PYTHON
)

echo.
goto :INSTALL_REQS

:: ---------------------------------------------------
:: Ask if user wants auto-install
:: ---------------------------------------------------
:ASK_INSTALL_PYTHON
echo. >> "%LOGFILE%"
echo [LOG] Asking user to install Python... >> "%LOGFILE%"
echo.
echo Python not found on your system.
echo Do you want to download and install Python 3.11.9?
echo.
choice /c YN /n /m " [Y] Yes, install Python 3.11.9    [N] No, I'll install it myself "
if %errorlevel%==1 (
    echo [LOG] User chose YES >> "%LOGFILE%"
    goto :INSTALL_PYTHON
)
if %errorlevel%==2 (
    echo [LOG] User chose NO >> "%LOGFILE%"
    goto :MANUAL_PYTHON
)

:: ---------------------------------------------------
:: Download and install Python 3.11.9
:: ---------------------------------------------------
:INSTALL_PYTHON
echo. >> "%LOGFILE%"
echo [LOG] Starting Python download... >> "%LOGFILE%"
echo.
echo [+] Downloading Python 3.11.9 (64-bit)...
set "INSTALLER_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
set "INSTALLER_PATH=%TEMP%\python-3.11.9-installer.exe"

echo [LOG] URL: %INSTALLER_URL% >> "%LOGFILE%"

powershell -Command "$ProgressPreference='SilentlyContinue'; Invoke-WebRequest -Uri '%INSTALLER_URL%' -OutFile '%INSTALLER_PATH%' -UseBasicParsing"

if not exist "%INSTALLER_PATH%" (
    echo.
    echo [ERROR] Download failed!
    echo [ERROR] Download failed >> "%LOGFILE%"
    echo.
    echo Please install Python manually:
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Download complete.
echo [LOG] Download OK >> "%LOGFILE%"
echo [+] Installing Python 3.11.9...
echo [LOG] Installing Python... >> "%LOGFILE%"

start /wait "" "%INSTALLER_PATH%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1

del "%INSTALLER_PATH%" 2>nul
echo [LOG] Python installed >> "%LOGFILE%"

echo [OK] Python installed!
echo [+] Updating environment...
echo [LOG] Refreshing PATH from registry... >> "%LOGFILE%"

:: Refresh PATH from registry
for /f "skip=2 tokens=3*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path 2^>nul') do set "SYSTEM_PATH=%%a %%b"
for /f "skip=2 tokens=3*" %%a in ('reg query "HKCU\Environment" /v Path 2^>nul') do set "USER_PATH=%%a %%b"
set "PATH=%SYSTEM_PATH%;%USER_PATH%"

echo [LOG] PATH updated from registry >> "%LOGFILE%"
echo [OK] Environment updated!
echo.
goto :INSTALL_REQS

:: ---------------------------------------------------
:: User wants manual installation
:: ---------------------------------------------------
:MANUAL_PYTHON
echo.
echo OK - please install Python 3.11 or 3.12 from:
echo https://www.python.org/downloads/
echo.
echo Make sure to check "Add Python to PATH"!
echo.
echo Then run this setup.bat again.
echo.
echo [LOG] Manual installation chosen >> "%LOGFILE%"
pause
exit /b 0

:: ---------------------------------------------------
:: Install packages
:: ---------------------------------------------------
:INSTALL_REQS
echo [2/3] Installing packages (3-10 minutes)...
echo [2/3] Installing packages... >> "%LOGFILE%"
echo.

:: Check if requirements.txt exists
if not exist "%~dp0requirements.txt" (
    echo [ERROR] requirements.txt not found!
    echo [ERROR] requirements.txt not found in %~dp0 >> "%LOGFILE%"
    echo.
    echo Please make sure you're running setup.bat from the GearCrate directory.
    echo.
    pause
    exit /b 1
)

echo [LOG] Upgrading pip... >> "%LOGFILE%"
python -m pip install --upgrade pip --quiet

echo [LOG] Installing requirements.txt... >> "%LOGFILE%"
echo This may take several minutes...
echo.
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo =========================================
    echo [ERROR] Package installation failed!
    echo =========================================
    echo.
    echo [ERROR] pip install failed >> "%LOGFILE%"
    echo.
    echo Common solutions:
    echo.
    echo 1. If you see "Unknown compiler" or "meson" errors:
    echo    - Python 3.14 is too new! Use Python 3.11 or 3.12
    echo    - Uninstall Python 3.14 and run setup.bat again
    echo.
    echo 2. If requirements.txt was not found:
    echo    - Make sure you're in the GearCrate folder
    echo    - Right-click setup.bat and "Run as Administrator"
    echo.
    echo 3. For other errors:
    echo    - Check setup-log.txt for details
    echo    - Try: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo [LOG] All packages installed >> "%LOGFILE%"

:: ---------------------------------------------------
:: Done
:: ---------------------------------------------------
echo.
echo =========================================
echo        INSTALLATION COMPLETE!
echo =========================================
echo.
echo Start GearCrate with:
echo.
echo       start-desktop-admin.bat
echo.
echo.
echo Happy hunting in Star Citizen!
echo.
echo [LOG] Setup completed >> "%LOGFILE%"
echo [LOG] Finished: %date% %time% >> "%LOGFILE%"
pause
