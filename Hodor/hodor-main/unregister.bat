@echo off
:: ============================================
:: Unregister the Unlock Credential Provider
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
set DLL_DEST=C:\Windows\System32\UnlockProvider.dll

echo [INFO] Removing credential provider registration...
reg delete "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\Credential Providers\%GUID%" /f >nul 2>&1

echo [INFO] Removing COM registration...
reg delete "HKLM\SOFTWARE\Classes\CLSID\%GUID%" /f >nul 2>&1

echo [INFO] Removing DLL from System32...
del /f "%DLL_DEST%" >nul 2>&1

echo.
echo ============================================
echo  Unregistration Complete!
echo ============================================
echo.
echo  The Unlock Provider has been removed.
echo  The change takes effect on the next lock screen.
echo ============================================
pause
