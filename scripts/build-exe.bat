@echo off
REM Windows 打包脚本
echo ==========================================
echo 开始打包 NASPT 为单文件 EXE
echo ==========================================

REM 检查是否安装了 PyInstaller
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 错误: 未安装 PyInstaller
    echo 正在安装 PyInstaller...
    pip install pyinstaller
)

REM 清理之前的构建
cd /d %~dp0\..
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist naspt.spec del naspt.spec

echo.
echo 开始打包...
pyinstaller scripts\build-exe.spec

if errorlevel 1 (
    echo.
    echo ==========================================
    echo 打包失败！
    echo ==========================================
    pause
    exit /b 1
)

echo.
echo ==========================================
echo 打包完成！
echo ==========================================
echo EXE 文件位置: dist\naspt.exe
echo.
echo 文件大小:
dir dist\naspt.exe
echo.
pause

