@echo off
echo 开始构建安卓应用...

REM 确保已安装buildozer
pip install buildozer

REM 切换到buildozer.spec所在目录
cd /d %~dp0

REM 执行buildozer命令构建APK
buildozer android debug

echo 构建完成！
echo APK文件位于 bin 目录中
pause