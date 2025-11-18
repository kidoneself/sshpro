@echo off
chcp 65001 >nul
REM Windows build script for NASPT EXE
echo ==========================================
echo Building NASPT as single EXE file
echo ==========================================

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Error: PyInstaller not installed
    echo Installing PyInstaller...
    python -m pip install pyinstaller
)

REM Clean previous builds
cd /d %~dp0\..
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist naspt.spec del naspt.spec

echo.
echo Starting build...
pyinstaller scripts\build-exe.spec

if errorlevel 1 (
    echo.
    echo ==========================================
    echo Build failed!
    echo ==========================================
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Build completed!
echo ==========================================
echo EXE file location: dist\naspt.exe
echo.
echo File size:
dir dist\naspt.exe
echo.
pause
