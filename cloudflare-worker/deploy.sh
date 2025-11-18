#!/bin/bash

# NASPT Services Worker 部署脚本

echo "================================"
echo "NASPT 服务配置生成器部署工具"
echo "================================"
echo ""

# 检查 wrangler 是否安装
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler 未安装"
    echo ""
    echo "请先安装 Wrangler："
    echo "  npm install -g wrangler"
    echo ""
    exit 1
fi

echo "✅ Wrangler 已安装"
echo ""

# 检查是否已登录
echo "检查登录状态..."
if ! wrangler whoami &> /dev/null; then
    echo "❌ 未登录 Cloudflare"
    echo ""
    echo "正在打开登录页面..."
    wrangler login
    echo ""
fi

echo "✅ 已登录 Cloudflare"
echo ""

# 选择部署方式
echo "请选择部署方式："
echo "1. 部署到生产环境"
echo "2. 本地开发测试"
echo ""
read -p "请输入选项 (1 或 2): " choice

case $choice in
    1)
        echo ""
        echo "开始部署到生产环境..."
        wrangler deploy
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "================================"
            echo "✅ 部署成功！"
            echo "================================"
            echo ""
            echo "你的 Worker 已上线，访问地址会显示在上方输出中"
            echo ""
            echo "示例: https://naspt-services.your-account.workers.dev"
            echo ""
        else
            echo ""
            echo "❌ 部署失败，请查看错误信息"
            exit 1
        fi
        ;;
    2)
        echo ""
        echo "启动本地开发服务器..."
        echo "按 Ctrl+C 停止服务"
        echo ""
        wrangler dev
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
