#!/usr/bin/env python3
"""
Google Colab构建脚本
在 https://colab.research.google.com/ 中运行此脚本
"""

import os
import subprocess
import zipfile
from google.colab import files

print("在Google Colab中构建Android应用...")

# 上传项目文件
print("请上传项目文件（包括main.py和buildozer.spec）...")
uploaded = files.upload()

# 解压文件
for filename in uploaded.keys():
    if filename.endswith('.zip'):
        with zipfile.ZipFile(filename, 'r') as zip_ref:
            zip_ref.extractall('.')
        print(f"已解压 {filename}")

# 安装buildozer
print("安装buildozer...")
subprocess.run(['pip', 'install', 'buildozer'], check=True)

# 构建Android应用
print("开始构建APK...")
result = subprocess.run(['buildozer', '-v', 'android', 'debug'], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("错误信息:", result.stderr)

# 下载生成的APK
if os.path.exists('bin'):
    apk_files = [f for f in os.listdir('bin') if f.endswith('.apk')]
    if apk_files:
        apk_file = apk_files[0]
        print(f"下载APK文件: {apk_file}")
        files.download(f'bin/{apk_file}')
    else:
        print("未找到APK文件")
else:
    print("bin目录不存在，构建可能失败")