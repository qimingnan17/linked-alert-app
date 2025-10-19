#!/bin/bash

echo "在WSL2中构建Android应用..."

# 检查是否在WSL环境中
if [[ ! -f /proc/version ]] || ! grep -qi "microsoft" /proc/version; then
    echo "错误：请在WSL2环境中运行此脚本"
    exit 1
fi

# 更新包管理器
echo "更新系统包..."
sudo apt update

# 安装依赖
echo "安装构建依赖..."
sudo apt install -y python3 python3-pip git wget unzip openjdk-8-jdk zlib1g-dev

# 安装buildozer
echo "安装buildozer..."
pip3 install buildozer

# 构建Android应用
echo "开始构建APK..."
buildozer -v android debug

echo "构建完成！APK文件位于 bin 目录中"