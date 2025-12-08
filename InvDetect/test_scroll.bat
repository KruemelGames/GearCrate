@echo off
:: Test script for dynamic scroll calculation
:: Usage: test_scroll.bat [max_scrolls]
:: Example: test_scroll.bat 5  (performs 5 scrolls)
:: Default: 10 scrolls

echo.
echo ===================================================================
echo   SCROLL CALCULATION TEST
echo ===================================================================
echo.
echo This will test the dynamic scroll calculation WITHOUT scanning items.
echo.
echo Instructions:
echo   1. Start Star Citizen and open Universal Inventory
echo   2. Press INSERT to start the test
echo   3. Press DELETE to stop the test
echo   4. Check scan_log.txt for detailed results
echo.
echo ===================================================================
echo.

:: Check if max_scrolls argument provided, otherwise default to 10
set MAX_SCROLLS=%1
if "%MAX_SCROLLS%"=="" set MAX_SCROLLS=10

echo Max scrolls: %MAX_SCROLLS%
echo.

:: Run test with Python
python test_scroll.py %MAX_SCROLLS%

pause
