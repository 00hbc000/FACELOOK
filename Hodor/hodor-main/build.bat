@echo off
setlocal

echo ============================================
echo  Unlock Credential Provider - Build Script
echo  VS2022 x64 Command Line Toolchain
echo ============================================
echo.

:: Try to find vcvarsall.bat in common VS2022 locations
set "VCVARSALL="
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARSALL=C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvarsall.bat"
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARSALL=C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvarsall.bat"
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARSALL=C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvarsall.bat"
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" (
    set "VCVARSALL=C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat"
)

if "%VCVARSALL%"=="" (
    echo [ERROR] Could not find VS2022 vcvarsall.bat
    echo Please set VCVARSALL environment variable or install VS2022 Build Tools.
    exit /b 1
)

echo [INFO] Using: %VCVARSALL%
call "%VCVARSALL%" x64
if errorlevel 1 (
    echo [ERROR] Failed to initialize VS2022 x64 environment.
    exit /b 1
)
echo.

:: Clean previous build
echo [INFO] Cleaning previous build artifacts...
if exist *.obj del /q *.obj
if exist UnlockProvider.dll del /q UnlockProvider.dll
if exist UnlockProvider.lib del /q UnlockProvider.lib
if exist UnlockProvider.exp del /q UnlockProvider.exp
if exist test_unlock.exe del /q test_unlock.exe
echo.

:: -----------------------------------------------
:: Build the Credential Provider DLL
:: -----------------------------------------------
echo [BUILD] Compiling credential provider sources...
cl.exe /nologo /W4 /WX- /EHsc /MT /O2 /DWIN32 /D_WINDOWS /DUNICODE /D_UNICODE ^
    /DNTDDI_VERSION=0x0A000000 /D_WIN32_WINNT=0x0A00 ^
    /c Dll.cpp ClassFactory.cpp UnlockProvider.cpp UnlockCredential.cpp ^
    PipeListener.cpp helpers.cpp
if errorlevel 1 (
    echo.
    echo [ERROR] Compilation failed.
    exit /b 1
)
echo [OK] Compilation succeeded.
echo.

echo [BUILD] Linking UnlockProvider.dll...
link.exe /nologo /DLL /OUT:UnlockProvider.dll /DEF:UnlockProvider.def ^
    Dll.obj ClassFactory.obj UnlockProvider.obj UnlockCredential.obj ^
    PipeListener.obj helpers.obj ^
    ole32.lib advapi32.lib secur32.lib user32.lib kernel32.lib ^
    uuid.lib shlwapi.lib
if errorlevel 1 (
    echo.
    echo [ERROR] Linking DLL failed.
    exit /b 1
)
echo [OK] UnlockProvider.dll built successfully.
echo.

:: -----------------------------------------------
:: Build the test application
:: -----------------------------------------------
echo [BUILD] Compiling test application...
cl.exe /nologo /W4 /WX- /EHsc /MT /O2 /DWIN32 /D_WINDOWS ^
    test_unlock.cpp /Fe:test_unlock.exe /link advapi32.lib user32.lib kernel32.lib
if errorlevel 1 (
    echo.
    echo [ERROR] Test app compilation failed.
    exit /b 1
)
echo [OK] test_unlock.exe built successfully.
echo.

:: Clean up .obj files
del /q *.obj 2>nul

echo ============================================
echo  Build Complete!
echo ============================================
echo.
echo  Output files:
echo    UnlockProvider.dll  - Credential Provider
echo    test_unlock.exe     - Test Application
echo.
echo  Next steps:
echo    1. Run register.bat as Administrator
echo    2. Lock screen (Win+L)
echo    3. Run: test_unlock.exe ^<username^> ^<password^>
echo ============================================
