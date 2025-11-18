#!/bin/bash
# Linux/macOS 打包脚本（用于测试，Windows请使用build-exe.bat）

set -e

echo "=========================================="
echo "开始打包 NASPT 为单文件 EXE"
echo "=========================================="

# 检查是否安装了 PyInstaller
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "错误: 未安装 PyInstaller"
    echo "正在安装 PyInstaller..."
    pip3 install pyinstaller
fi

# 清理之前的构建
rm -rf build dist naspt.spec

echo ""
echo "开始打包..."
cd "$(dirname "$0")/.."
pyinstaller scripts/build-exe.spec

if [ $? -ne 0 ]; then
    echo ""
    echo "=========================================="
    echo "打包失败！"
    echo "=========================================="
    exit 1
fi

echo ""
echo "=========================================="
echo "打包完成！"
echo "=========================================="
echo "EXE 文件位置: dist/naspt"
echo ""
echo "文件大小:"
ls -lh dist/naspt
echo ""

