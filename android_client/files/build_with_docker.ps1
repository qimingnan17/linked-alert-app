Write-Host "使用Docker构建Android应用..." -ForegroundColor Green

# 检查Docker是否安装
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "错误：Docker未安装！" -ForegroundColor Red
    Write-Host "请先安装Docker Desktop：https://docs.docker.com/desktop/install/windows-install/" -ForegroundColor Yellow
    exit 1
}

# 创建Dockerfile
$dockerfileContent = @"
FROM ubuntu:20.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive

# 更新包管理器并安装依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    wget \
    unzip \
    openjdk-8-jdk \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装buildozer
RUN pip3 install buildozer

# 创建工作目录
WORKDIR /app

# 复制项目文件
COPY . .

# 构建Android应用
CMD ["buildozer", "-v", "android", "debug"]
"@

Set-Content -Path "Dockerfile" -Value $dockerfileContent

Write-Host "构建Docker镜像..." -ForegroundColor Yellow
docker build -t kivy-android-builder .

Write-Host "运行Docker容器构建APK..." -ForegroundColor Yellow
docker run --rm -v "${PWD}/bin:/app/bin" kivy-android-builder

Write-Host "构建完成！APK文件位于 bin 目录中" -ForegroundColor Green