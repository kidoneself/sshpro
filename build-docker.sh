#!/bin/bash

# Docker 多架构构建脚本
# 支持 amd64 和 arm64 架构

set -e

IMAGE_NAME="naspt"
IMAGE_TAG="${1:-latest}"
REGISTRY="${2:-}"

# 如果没有指定 registry，则使用本地构建
if [ -z "$REGISTRY" ]; then
    FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
else
    FULL_IMAGE_NAME="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
fi

echo "=========================================="
echo "构建 Docker 镜像: ${FULL_IMAGE_NAME}"
echo "架构: linux/amd64, linux/arm64"
echo "=========================================="

# 检查是否安装了 buildx
if ! docker buildx version > /dev/null 2>&1; then
    echo "错误: 需要安装 Docker Buildx"
    echo "请运行: docker buildx install"
    exit 1
fi

# 创建并使用 buildx builder（如果不存在）
BUILDER_NAME="multiarch-builder"
if ! docker buildx ls | grep -q "$BUILDER_NAME"; then
    echo "创建 buildx builder: $BUILDER_NAME"
    docker buildx create --name "$BUILDER_NAME" --use
else
    echo "使用现有 buildx builder: $BUILDER_NAME"
    docker buildx use "$BUILDER_NAME"
fi

# 启动 builder
docker buildx inspect --bootstrap

# 构建多架构镜像
echo ""
echo "开始构建多架构镜像..."

docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --tag "${FULL_IMAGE_NAME}" \
    --push \
    .

echo ""
echo "=========================================="
echo "✓ 构建完成！"
echo "镜像: ${FULL_IMAGE_NAME}"
echo "架构: linux/amd64, linux/arm64"
echo "=========================================="

# 如果指定了 registry，显示拉取命令
if [ -n "$REGISTRY" ]; then
    echo ""
    echo "拉取镜像命令:"
    echo "  docker pull ${FULL_IMAGE_NAME}"
fi

