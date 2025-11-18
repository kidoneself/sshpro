#!/bin/bash

# Docker 本地单架构构建脚本（用于测试）
# 根据当前系统架构构建

set -e

IMAGE_NAME="naspt"
IMAGE_TAG="${1:-latest}"

FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo "=========================================="
echo "构建 Docker 镜像（本地）: ${FULL_IMAGE_NAME}"
echo "=========================================="

# 构建镜像
docker build -t "${FULL_IMAGE_NAME}" .

echo ""
echo "=========================================="
echo "✓ 构建完成！"
echo "镜像: ${FULL_IMAGE_NAME}"
echo ""
echo "运行容器:"
echo "  docker run -d -p 15432:15432 --name naspt ${FULL_IMAGE_NAME}"
echo "=========================================="

