@echo off
:: ============================================
:: Register the Unlock Credential Provider
:: Must be run as Administrator
:: ============================================

net session >nul 2>&1
if errorlevel 1 (
    echo [ERROR] This script must be run as Administrator.
    echo Right-click and select "Run as administrator".
    pause
    exit /b 1
)

set GUID={E0A8C5B2-9F3D-4E7A-B1C6-8D2F5A3E9B70}
set DLL_SRC=%~dp0UnlockProvider.dll
set DLL_DEST=C:\Windows\System32\UnlockProvider.dll

if not exist "%DLL_SRC%" (
    echo [ERROR] UnlockProvider.dll not found. Run build.bat first.
    pause
    exit /b 1
)

echo [INFO] Copying DLL to System32...
copy /Y "%DLL_SRC%" "%DLL_DEST%"
if errorlevel 1 (
    echo [ERROR] Failed to copy DLL to System32.
    pause
    exit /b 1
)

echo [INFO] Registering COM server...
reg add "HKLM\SOFTWARE\Classes\CLSID\%GUID%" /ve /d "UnlockProvider" /f >nul
reg add "HKLM\SOFTWARE\Classes\CLSID\%GUID%\InprocServer32" /ve /d "%DLL_DEST%" /f >nul
reg add "HKLM\SOFTWARE\Classes\CLSID\%GUID%\InprocServer32" /v ThreadingModel /d "Apartment" /f >nul

echo [INFO] Registering credential provider...
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\Credential Providers\%GUID%" /ve /d "UnlockProvider" /f >nul

echo.
echo ============================================
echo  Registration Complete!
echo ============================================
echo.
echo  The Unlock Provider will appear on the next
echo  lock screen / logon screen.
echo.
echo  To test:
echo    test_unlock.exe ^<username^> ^<password^>
echo.
echo  To unregister:
echo    unregister.bat (as Administrator)
echo ============================================
pause
