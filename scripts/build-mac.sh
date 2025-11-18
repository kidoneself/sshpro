#!/bin/bash
# macOS 打包脚本

set -e

echo "=========================================="
echo "Building NASPT as macOS Application"
echo "=========================================="

# 检查是否安装了 PyInstaller
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "Error: PyInstaller not installed"
    echo "Installing PyInstaller..."
    pip3 install pyinstaller
fi

# 获取项目根目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# 清理之前的构建
rm -rf build dist naspt.spec

echo ""
echo "Starting build..."
python3 -m PyInstaller scripts/build-mac.spec

if [ $? -ne 0 ]; then
    echo ""
    echo "=========================================="
    echo "Build failed!"
    echo "=========================================="
    exit 1
fi

# 重命名 .app bundle（如果 PyInstaller 创建的是目录而不是 .app）
if [ -d "dist/naspt" ] && [ ! -d "dist/naspt.app" ]; then
    mv dist/naspt dist/naspt.app
fi

# 清理临时文件
rm -rf dist/naspt-temp

echo ""
echo "=========================================="
echo "Build completed!"
echo "=========================================="
echo "Application location: dist/naspt.app"
echo ""
echo "File size:"
du -sh dist/naspt.app
echo ""
echo "To run the app:"
echo "  open dist/naspt.app"
echo ""

