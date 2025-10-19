from kivy.utils import platform
from kivy.clock import Clock
import threading
import time

class ResponseHandler:
    def __init__(self, log_callback=None):
        """
        初始化响应处理器
        
        Args:
            log_callback: 日志回调函数
        """
        self.log_callback = log_callback
    
    def handle_message(self, message):
        """
        处理接收到的消息
        
        Args:
            message: 接收到的消息字典
        """
        if not isinstance(message, dict):
            self.log("收到无效消息格式")
            return
        
        # 根据消息类型分发处理
        msg_type = message.get('type')
        
        if msg_type == 'alert':
            self.handle_alert(message)
        elif msg_type == 'command':
            self.handle_command(message)
        elif msg_type in ['connection', 'disconnection', 'error', 'info']:
            # 系统消息直接记录日志
            self.log(message.get('message', '系统消息'))
        else:
            # 未知消息类型
            source = message.get('source', {})
            source_ip = source.get('ip', 'unknown')
            self.log(f"收到来自 {source_ip} 的未知类型消息: {message}")
    
    def handle_alert(self, message):
        """
        处理警报消息
        
        Args:
            message: 警报消息字典
        """
        content = message.get('content', '未指定内容')
        level = message.get('level', 'info')
        source = message.get('source', {})
        source_ip = source.get('ip', 'unknown')
        
        # 记录警报日志
        self.log(f"警报 [{level}] 来自 {source_ip}: {content}")
        
        # 根据警报级别执行不同响应
        if level == 'critical':
            # 关键警报：声音+震动+闪光
            self.play_sound(duration=3, repeat=3)
            self.vibrate(duration=1, repeat=3)
            self.flash_screen(color=[1, 0, 0, 1], count=5)  # 红色闪烁
        elif level == 'warning':
            # 警告：声音+震动
            self.play_sound(duration=1, repeat=2)
            self.vibrate(duration=0.5, repeat=2)
            self.flash_screen(color=[1, 0.5, 0, 1], count=3)  # 橙色闪烁
        elif level == 'info':
            # 信息：声音
            self.play_sound(duration=0.5)
            self.flash_screen(color=[0, 0, 1, 1], count=2)  # 蓝色闪烁
    
    def handle_command(self, message):
        """
        处理命令消息
        
        Args:
            message: 命令消息字典
        """
        command = message.get('command')
        params = message.get('params', {})
        source = message.get('source', {})
        source_ip = source.get('ip', 'unknown')
        
        self.log(f"执行命令 '{command}' 来自 {source_ip}, 参数: {params}")
        
        # 根据命令类型执行不同操作
        if command == 'beep':
            duration = params.get('duration', 1)
            repeat = params.get('repeat', 1)
            self.play_sound(duration=duration, repeat=repeat)
        elif command == 'vibrate':
            duration = params.get('duration', 1)
            repeat = params.get('repeat', 1)
            self.vibrate(duration=duration, repeat=repeat)
        elif command == 'flash':
            count = params.get('count', 3)
            color = params.get('color', [1, 0, 0, 1])  # 默认红色
            self.flash_screen(color=color, count=count)
        elif command == 'display':
            text = params.get('text', '')
            duration = params.get('duration', 5)
            self.display_message(text, duration)
        else:
            self.log(f"未知命令: {command}")
    
    def play_sound(self, duration=1, repeat=1):
        """
        播放警报声音
        
        Args:
            duration: 声音持续时间(秒)
            repeat: 重复次数
        """
        self.log(f"播放警报声音，持续 {duration} 秒，重复 {repeat} 次")
        
        # 在安卓平台上使用Android API播放声音
        if platform == 'android':
            try:
                from jnius import autoclass
                # 获取Android ToneGenerator类
                ToneGenerator = autoclass('android.media.ToneGenerator')
                AudioManager = autoclass('android.media.AudioManager')
                
                # 创建ToneGenerator实例
                toneGenerator = ToneGenerator(AudioManager.STREAM_ALARM, 100)
                
                # 在后台线程中播放声音
                def play_tone():
                    for _ in range(repeat):
                        # 播放警报音
                        toneGenerator.startTone(ToneGenerator.TONE_CDMA_ALERT_CALL_GUARD, int(duration * 1000))
                        time.sleep(duration)
                        if repeat > 1:
                            time.sleep(0.5)  # 间隔
                    toneGenerator.release()
                
                threading.Thread(target=play_tone).start()
            except Exception as e:
                self.log(f"播放声音失败: {str(e)}")
        else:
            # 非安卓平台，可以使用Kivy的音频功能
            try:
                from kivy.core.audio import SoundLoader
                sound = SoundLoader.load('alert.wav')  # 需要提供一个警报音频文件
                if sound:
                    sound.volume = 1
                    sound.play()
            except:
                self.log("播放声音失败: 未找到音频文件或不支持的平台")
    
    def vibrate(self, duration=1, repeat=1):
        """
        设备震动
        
        Args:
            duration: 震动持续时间(秒)
            repeat: 重复次数
        """
        self.log(f"设备震动，持续 {duration} 秒，重复 {repeat} 次")
        
        # 在安卓平台上使用Android API控制震动
        if platform == 'android':
            try:
                from jnius import autoclass
                from android.permissions import request_permissions, Permission
                
                # 请求震动权限
                request_permissions([Permission.VIBRATE])
                
                # 获取Android Vibrator服务
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                Context = autoclass('android.content.Context')
                vibrator = activity.getSystemService(Context.VIBRATOR_SERVICE)
                
                # 在后台线程中控制震动
                def vibrate_device():
                    for _ in range(repeat):
                        vibrator.vibrate(int(duration * 1000))
                        time.sleep(duration)
                        if repeat > 1:
                            time.sleep(0.2)  # 间隔
                
                threading.Thread(target=vibrate_device).start()
            except Exception as e:
                self.log(f"震动失败: {str(e)}")
        else:
            self.log("震动功能仅在安卓设备上可用")
    
    def flash_screen(self, color=[1, 0, 0, 1], count=3):
        """
        屏幕闪烁
        
        Args:
            color: RGBA颜色值
            count: 闪烁次数
        """
        self.log(f"屏幕闪烁 {count} 次")
        
        # 这个功能需要在主应用中实现，这里只提供接口
        # 在实际应用中，需要在主应用类中添加一个覆盖整个屏幕的Widget，
        # 然后通过改变其背景色和可见性来实现闪烁效果
        pass
    
    def display_message(self, text, duration=5):
        """
        显示消息
        
        Args:
            text: 要显示的文本
            duration: 显示持续时间(秒)
        """
        self.log(f"显示消息: {text}，持续 {duration} 秒")
        
        # 这个功能需要在主应用中实现，这里只提供接口
        # 在实际应用中，需要在主应用类中添加一个消息显示区域，
        # 然后通过更新其内容和可见性来实现消息显示
        pass
    
    def log(self, message):
        """记录日志"""
        if self.log_callback:
            # 确保在主线程中调用回调
            Clock.schedule_once(lambda dt: self.log_callback(message), 0)