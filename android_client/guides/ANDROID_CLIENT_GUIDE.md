# Android客户端使用指南

## 概述
Android客户端是联动警报系统的用户终端，负责接收服务器发送的警报信息并提供友好的用户界面。

## 主要功能
- 实时接收服务器警报信息
- 显示警报级别（info/warning/critical）
- 支持中文显示
- 警报声音提示
- 警报历史记录

## 文件结构
```
android_client/
├── main.py              # 主程序入口
├── network.py          # 网络通信模块
├── response_handler.py  # 响应处理模块
├── build_android.bat   # Android打包脚本
├── buildozer.spec      # Android打包配置
└── data/               # 资源文件
    ├── audio/          # 音频文件
    └── fonts/          # 字体文件
```

## 快速启动

### Windows环境运行
```bash
cd android_client
python main.py
```

### Android设备打包
```bash
cd android_client
build_android.bat
```

## 配置说明

### 服务器连接配置
在`network.py`中配置服务器地址和端口：
```python
SERVER_HOST = "127.0.0.1"  # 服务器IP地址
SERVER_PORT = 9999         # 服务器端口
```

### 警报级别显示
- **info**：蓝色，信息性警报
- **warning**：黄色，警告警报  
- **critical**：红色，严重警报

## 使用说明

### 1. 启动客户端
运行`main.py`后，客户端会自动连接服务器并开始监听警报。

### 2. 接收警报
当服务器发送警报时，客户端会：
- 显示警报信息
- 播放提示音
- 记录警报历史

### 3. 界面操作
- 查看当前警报状态
- 浏览警报历史记录
- 清除已读警报

## 故障排除

### 连接失败
1. 检查服务器是否正常运行
2. 确认网络连接正常
3. 检查防火墙设置

### 显示异常
1. 确保字体文件存在
2. 检查Kivy依赖是否正确安装

## 开发说明

### 添加新功能
1. 在`main.py`中扩展界面功能
2. 在`response_handler.py`中添加新的消息处理逻辑
3. 在`network.py`中扩展通信协议

### 自定义警报样式
修改`main.py`中的警报显示逻辑，自定义颜色、字体和动画效果。