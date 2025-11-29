@echo off
echo ================================================================================
echo    QUICK BULK IMPORT - Star Citizen Inventory Manager
echo ================================================================================
echo.
echo Dieses Tool importiert Items direkt von CStone.space in deine Datenbank.
echo.
echo HINWEIS: Die Items werden mit Count=0 importiert (nicht im Inventar sichtbar).
echo          Du kannst sie danach im Inventar-Manager auf die gewuenschte Anzahl setzen.
echo.
echo ================================================================================
echo.

python quick_bulk_import.py

echo.
echo ================================================================================
echo Import abgeschlossen!
echo.
echo Druecke eine beliebige Taste um das Fenster zu schliessen...
pause > nul
