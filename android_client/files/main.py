# -*- coding: utf-8 -*-
import sys
import os
import socket
import threading
import json
import time
from datetime import datetime

# 音频播放和硬件控制相关导入
try:
    from kivy.core.audio import SoundLoader
    import androidhelper
    droid = androidhelper.Android()
    ANDROID_AVAILABLE = True
    print("检测到Android环境")
except ImportError:
    print("未检测到Android环境，将使用模拟模式")
    ANDROID_AVAILABLE = False
    droid = None

# 创建音频文件夹
audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'audio')
if not os.path.exists(audio_dir):
    os.makedirs(audio_dir)
    print(f"已创建音频文件夹: {audio_dir}")

# 警报状态
is_alert_active = False
current_alert_sound = None
alert_stop_event = threading.Event()

# 添加初始诊断信息
print(f"Python 版本: {sys.version}")
print(f"当前工作目录: {os.getcwd()}")
print("开始导入 Kivy 模块...")

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.utils import platform
from kivy.config import Config
from kivy.resources import resource_add_path
from kivy.core.text import LabelBase

# 确保正确处理UTF-8编码
if hasattr(sys, 'getfilesystemencoding'):
    encoding = sys.getfilesystemencoding()
    if encoding.lower() != 'utf-8':
        # 强制使用UTF-8编码
        os.environ['PYTHONIOENCODING'] = 'utf-8'

# 设置窗口大小
Window.size = (400, 600)

# 配置Kivy以支持中文
Config.set('kivy', 'log_level', 'error')

# 添加字体资源路径，让Kivy可以找到系统字体
if platform == 'win':
    # Windows系统下添加系统字体目录
    font_dirs = [
        'C:\\Windows\\Fonts',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'fonts')
    ]
    for font_dir in font_dirs:
        if os.path.exists(font_dir):
            resource_add_path(font_dir)
            print(f"已添加字体目录: {font_dir}")

print(f"当前平台: {platform}")
print("使用系统默认字体并配置字体路径，确保中文显示正确")

# 设置默认字体配置
os.environ['KIVY_FONT_PATH'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'fonts')
print(f"Kivy字体路径设置为: {os.environ['KIVY_FONT_PATH']}")

# 尝试注册一些系统中常见的中文字体，但使用try-except避免可能的错误
try:
    # 尝试使用Windows系统中常见的中文字体
    if platform == 'win':
        common_fonts = [
            ('SimHei', 'simhei.ttf'),
            ('Microsoft YaHei', 'msyh.ttc'),
            ('Arial Unicode MS', 'arialuni.ttf'),
            ('SimSun', 'simsun.ttc')
        ]
        
        for font_name, font_file in common_fonts:
            font_path = os.path.join('C:\\Windows\\Fonts', font_file)
            if os.path.exists(font_path):
                print(f"尝试加载字体: {font_name} ({font_path})")
                # 注意：这里只是打印信息，不实际调用LabelBase.register以避免闪退
                # 而是通过系统默认字体机制处理
                os.environ['KIVY_DEFAULT_FONT'] = font_name
                print(f"已设置默认字体: {font_name}")
                break
except Exception as e:
    print(f"字体处理过程中出现警告（非严重错误）: {str(e)}")
    print("继续使用系统默认字体机制")

# 创建一个字体样式字典供UI组件使用
default_font_style = {
    'font_name': os.environ.get('KIVY_DEFAULT_FONT', 'sans-serif'),
    'font_size': '14sp'
}

class AlertClientApp(App):
    def build(self):
        print("构建应用界面...")
        self.title = u'联动警报客户端'
        self.server_ip = '0.0.0.0'  # 默认监听所有网络接口
        self.server_port = 8888     # 默认端口
        self.socket = None
        self.connection_thread = None
        self.is_listening = False
        
        # 警报相关状态
        self.is_alert_active = False
        self.current_alert_sound = None
        self.alert_stop_event = threading.Event()
        self.flash_thread = None
        self.alert_source = None  # 记录警报来源
        
        # 确保Window对象存在后设置回调
        if hasattr(Window, 'bind'):
            Window.bind(on_resume=self.on_resume)
            Window.bind(on_pause=self.on_pause)
        
        # 创建主布局
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 状态显示区域
        self.status_label = Label(
            text='状态: 未连接',
            size_hint=(1, 0.1),
            halign='left',
            valign='middle',
            **default_font_style
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        
        # 设置区域
        settings_box = BoxLayout(orientation='vertical', size_hint=(1, 0.3), spacing=5)
        
        # IP设置
        ip_box = BoxLayout(size_hint=(1, None), height=40)
        ip_box.add_widget(Label(text='监听IP:', size_hint=(0.3, 1), **default_font_style))
        self.ip_input = TextInput(
            text=self.server_ip,
            multiline=False,
            size_hint=(0.7, 1),
            font_name=default_font_style['font_name']
        )
        ip_box.add_widget(self.ip_input)
        
        # 端口设置
        port_box = BoxLayout(size_hint=(1, None), height=40)
        port_box.add_widget(Label(text='端口:', size_hint=(0.3, 1), **default_font_style))
        self.port_input = TextInput(
            text=str(self.server_port),
            multiline=False,
            size_hint=(0.7, 1),
            font_name=default_font_style['font_name']
        )
        port_box.add_widget(self.port_input)
        
        # 添加设置控件到设置区域
        settings_box.add_widget(ip_box)
        settings_box.add_widget(port_box)
        
        # 控制按钮
        control_box = BoxLayout(size_hint=(1, 0.15), spacing=10)
        self.start_button = Button(
            text='启动服务', 
            on_press=self.toggle_service,
            **default_font_style
        )
        control_box.add_widget(self.start_button)
        
        # 紧急停止警报按钮
        self.stop_alert_button = Button(
            text='停止警报', 
            on_press=self.stop_alert,
            **default_font_style,
            background_color=(0.9, 0.2, 0.2, 1)  # 红色背景
        )
        control_box.add_widget(self.stop_alert_button)
        
        # 日志区域
        log_label = Label(
            text='接收日志:', 
            size_hint=(1, 0.05), 
            halign='left',
            **default_font_style
        )
        log_label.bind(size=log_label.setter('text_size'))
        
        self.log_area = TextInput(
            text='',
            readonly=True,
            size_hint=(1, 0.4),
            background_color=(0.9, 0.9, 0.9, 1),
            font_name=default_font_style['font_name']
        )
        
        # 将所有组件添加到主布局
        layout.add_widget(self.status_label)
        layout.add_widget(settings_box)
        layout.add_widget(control_box)
        layout.add_widget(log_label)
        layout.add_widget(self.log_area)
        
        self.log_message("应用已启动")
        return layout
    
    def toggle_service(self, instance):
        if not self.is_listening:
            self.start_service()
        else:
            self.stop_service()
    
    def start_service(self):
        try:
            self.server_ip = self.ip_input.text
            self.server_port = int(self.port_input.text)
            
            # 创建套接字
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.server_ip, self.server_port))
            self.socket.listen(5)
            
            self.is_listening = True
            self.start_button.text = '停止服务'
            self.status_label.text = f'状态: 已启动 ({self.server_ip}:{self.server_port})'
            
            # 在新线程中接受连接
            self.connection_thread = threading.Thread(target=self.accept_connections)
            self.connection_thread.daemon = True
            self.connection_thread.start()
            
            self.log_message("服务已启动，等待连接...")
        except Exception as e:
            self.log_message(f"启动服务失败: {str(e)}")
    
    def stop_service(self):
        if self.socket:
            self.is_listening = False
            self.socket.close()
            self.socket = None
            self.start_button.text = '启动服务'
            self.status_label.text = '状态: 已停止'
            self.log_message("服务已停止")
    
    def accept_connections(self):
        while self.is_listening:
            try:
                client_socket, address = self.socket.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
                Clock.schedule_once(
                    lambda dt: self.log_message(f"接受来自 {address[0]}:{address[1]} 的连接"),
                    0
                )
            except:
                # 如果socket被关闭，退出循环
                break
    
    def handle_client(self, client_socket, address):
        try:
            while self.is_listening:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                # 处理接收到的数据
                self.process_data(data, client_socket, address)
        except:
            pass
        finally:
            client_socket.close()
    
    def process_data(self, data, client_socket, address):
        try:
            # 尝试解析JSON数据
            message = json.loads(data.decode('utf-8'))
            
            # 保存client_socket引用用于确认消息发送
            self.client_socket = client_socket
            
            # 在UI线程中更新日志
            Clock.schedule_once(
                lambda dt: self.log_message(f"收到来自 {address[0]} 的消息: {message}"),
                0
            )
            
            # 根据消息类型执行不同操作
            if 'type' in message:
                if message['type'] == 'alert':
                    # 直接启动综合警报
                    params = message.get('params', {})
                    self.start_alert(params)
                elif message['type'] == 'command':
                    command = message.get('command')
                    params = message.get('params', {})
                    
                    if command == 'alert':
                        self.start_alert(params)
                    elif command == 'stop_alert':
                        self.stop_alert()
                    else:
                        self.execute_command(command, params)
                
                # 发送响应
                response = {'status': 'ok', 'message': '已处理'}
                client_socket.send(json.dumps(response).encode('utf-8'))
        except json.JSONDecodeError:
            # 非JSON格式数据处理
            text_data = data.decode('utf-8', errors='ignore')
            Clock.schedule_once(
                lambda dt: self.log_message(f"收到非JSON数据: {text_data}"),
                0
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self.log_message(f"处理数据时出错: {str(e)}"),
                0
            )
    
    def handle_alert(self, message):
        """处理警报消息"""
        if 'content' in message:
            alert_content = message['content']
            level = message.get('level', 'info')
            
            # 在UI线程中显示警报
            Clock.schedule_once(
                lambda dt: self.show_alert(alert_content, level),
                0
            )
    
    def handle_command(self, message):
        """处理命令消息"""
        if 'command' in message:
            command = message['command']
            params = message.get('params', {})
            
            # 在UI线程中执行命令
            Clock.schedule_once(
                lambda dt: self.execute_command(command, params),
                0
            )
    
    def show_alert(self, content, level):
        """显示警报"""
        # 这里可以根据不同级别显示不同样式的警报
        self.log_message(f"警报 [{level}]: {content}")
        # TODO: 实现更丰富的警报展示效果
    
    def execute_command(self, command, params):
        """执行命令"""
        self.log_message(f"执行命令: {command}, 参数: {params}")
        
        # 根据不同命令执行不同操作
        if command == "beep":
            # 播放声音
            duration = params.get('duration', 1)
            self.log_message(f"播放警报声音，持续 {duration} 秒")
            self.play_sound(duration=duration)
        elif command == "vibrate":
            # 震动
            duration = params.get('duration', 1)
            self.log_message(f"设备震动，持续 {duration} 秒")
            self.vibrate(duration)
        elif command == "flash":
            # 闪光
            count = params.get('count', 3)
            self.log_message(f"闪光灯闪烁 {count} 次")
            self.flash_light(count)
        elif command == "alert":
            # 综合警报（声音+闪光灯+悬浮窗）
            self.log_message(f"启动综合警报")
            self.start_alert(params)
            # 发送确认消息到服务端，告知警报已启动
            self.send_alert_ack()
        elif command == "stop_alert":
            self.log_message("接收到停止警报命令")
            self.stop_alert()
            # 发送停止确认消息到服务端
            self.send_stop_alert_ack()
            
    def send_alert_ack(self):
        """发送警报启动确认到服务端"""
        try:
            if hasattr(self, 'client_socket') and self.client_socket:
                ack_message = json.dumps({"type": "alert_ack", "message": "警报已启动"})
                self.client_socket.send(ack_message.encode('utf-8'))
                self.log_message("已发送警报确认到服务端")
        except Exception as e:
            self.log_message(f"发送警报确认失败: {str(e)}")
    
    def send_stop_alert_ack(self):
        """发送警报停止确认到服务端"""
        try:
            if hasattr(self, 'client_socket') and self.client_socket:
                ack_message = json.dumps({"type": "stop_alert_ack", "message": "警报已停止"})
                self.client_socket.send(ack_message.encode('utf-8'))
                self.log_message("已发送停止警报确认到服务端")
        except Exception as e:
            self.log_message(f"发送停止警报确认失败: {str(e)}")
    
    def show_floating_window(self):
        """显示悬浮窗提示"""
        if ANDROID_AVAILABLE:
            try:
                self.log_message("显示悬浮窗提示")
                # 使用androidhelper显示通知，这是最简单可靠的方式
                droid.notify("紧急警报", "收到紧急警报，请立即处理！", "警报通知", timeout=30000)
                
                # 尝试创建悬浮窗（如果权限允许）
                try:
                    from jnius import autoclass, cast
                    
                    # 获取必要的Android类
                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                    WindowManager = autoclass('android.view.WindowManager')
                    LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
                    LinearLayout = autoclass('android.widget.LinearLayout')
                    TextView = autoclass('android.widget.TextView')
                    Button = autoclass('android.widget.Button')
                    Context = autoclass('android.content.Context')
                    Gravity = autoclass('android.view.Gravity')
                    
                    # 获取当前Activity
                    activity = PythonActivity.mActivity
                    
                    # 创建悬浮窗布局
                    linear_layout = LinearLayout(activity)
                    linear_layout.setOrientation(LinearLayout.VERTICAL)
                    linear_layout.setBackgroundColor(0xFFFF0000)  # 红色背景
                    
                    # 创建标题文本
                    title = TextView(activity)
                    title.setText("紧急警报")
                    title.setTextSize(24)
                    title.setTextColor(0xFFFFFFFF)
                    title.setPadding(20, 10, 20, 10)
                    
                    # 创建内容文本
                    content = TextView(activity)
                    content.setText("收到紧急警报，请立即处理！")
                    content.setTextSize(18)
                    content.setTextColor(0xFFFFFFFF)
                    content.setPadding(20, 10, 20, 10)
                    
                    # 创建关闭按钮
                    close_button = Button(activity)
                    close_button.setText("关闭警报")
                    close_button.setTextSize(16)
                    close_button.setPadding(20, 10, 20, 10)
                    
                    # 设置按钮点击事件 - 停止警报
                    def on_close_button_click(view):
                        self.stop_alert()
                        # 发送停止确认到服务端
                        self.send_stop_alert_ack()
                        # 移除悬浮窗
                        window_manager = cast(WindowManager, activity.getSystemService(Context.WINDOW_SERVICE))
                        window_manager.removeViewImmediate(linear_layout)
                    
                    # 创建点击监听器
                    class ButtonClickListener(autoclass('android.view.View$OnClickListener')):
                        def __init__(self, callback):
                            self.callback = callback
                            super(ButtonClickListener, self).__init__()
                        def onClick(self, view):
                            self.callback(view)
                    
                    close_button.setOnClickListener(ButtonClickListener(on_close_button_click))
                    
                    # 添加组件到布局
                    linear_layout.addView(title)
                    linear_layout.addView(content)
                    linear_layout.addView(close_button)
                    
                    # 设置悬浮窗参数
                    params = LayoutParams(
                        LayoutParams.WRAP_CONTENT,
                        LayoutParams.WRAP_CONTENT,
                        LayoutParams.TYPE_APPLICATION_OVERLAY,  # API 26+ 使用这个类型
                        LayoutParams.FLAG_NOT_FOCUSABLE | LayoutParams.FLAG_NOT_TOUCH_MODAL | LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH,
                        -3  # PixelFormat.TRANSLUCENT
                    )
                    
                    params.gravity = Gravity.TOP | Gravity.RIGHT
                    params.x = 20
                    params.y = 100
                    
                    # 添加悬浮窗
                    window_manager = cast(WindowManager, activity.getSystemService(Context.WINDOW_SERVICE))
                    window_manager.addView(linear_layout, params)
                    
                    # 保存悬浮窗引用以便后续可以移除
                    self.floating_window = linear_layout
                    self.log_message("悬浮窗已显示")
                    
                except Exception as floating_e:
                    self.log_message(f"创建悬浮窗失败，使用通知替代: {str(floating_e)}")
                    # 如果悬浮窗创建失败，确保通知已经发送
                    droid.notify("紧急警报", "收到紧急警报，请点击通知查看详情！", "警报通知", timeout=30000)
                    
            except Exception as e:
                self.log_message(f"显示提示出错: {str(e)}")
    
    def on_pause(self):
        """当应用进入后台时调用"""
        print("应用暂停")
        # 如果警报正在激活，显示悬浮窗和通知
        if hasattr(self, 'is_alert_active') and self.is_alert_active:
            self.show_floating_window("收到紧急警报，请立即处理！")
        # 保持服务运行，即使在后台
        return True  # 允许应用暂停
    
    def on_resume(self):
        """当应用从后台返回时调用"""
        # 如果有悬浮窗，移除它
        if hasattr(self, 'floating_window') and self.floating_window and ANDROID_AVAILABLE:
            try:
                from jnius import autoclass, cast
                Context = autoclass('android.content.Context')
                WindowManager = autoclass('android.view.WindowManager')
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                window_manager = cast(WindowManager, activity.getSystemService(Context.WINDOW_SERVICE))
                window_manager.removeViewImmediate(self.floating_window)
                self.floating_window = None
            except Exception as e:
                self.log_message(f"移除悬浮窗出错: {str(e)}")
        return True
    
    def log_message(self, message):
        """添加日志消息"""
        current_text = self.log_area.text
        self.log_area.text = f"{current_text}\n[{self.get_time()}] {message}" if current_text else f"[{self.get_time()}] {message}"
        # 滚动到底部
        self.log_area.cursor = (0, len(self.log_area.text))
    
    def get_time(self):
        """获取当前时间字符串"""
        return datetime.now().strftime("%H:%M:%S")
    
    def on_stop(self):
        """应用停止时清理资源"""
        print("应用正在停止...")
        self.stop_alert()
        self.stop_service()
        
    def on_pause(self):
        """应用暂停时"""
        print("应用暂停")
        # 保持服务运行，即使在后台
        return True
        
    def on_resume(self):
        """应用恢复时"""
        print("应用恢复")
        # 如果有活动的警报，显示提示
        if self.is_alert_active:
            self.show_notification("警报", "有活动的警报正在进行中")
        return True
        
    def play_sound(self, duration=3, sound_file=None):
        """播放警报声音"""
        try:
            if platform == 'win':
                # Windows平台测试用
                import winsound
                winsound.Beep(1000, duration * 1000)  # 1000Hz，持续指定秒数
            elif ANDROID_AVAILABLE:
                # 检查音频文件夹和文件
                audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'audio')
                alert_sound_path = os.path.join(audio_dir, 'alert_sound.mp3') if sound_file is None else sound_file
                
                # 支持的音频文件格式列表
                sound_formats = ['alert_sound.mp3', 'alert_sound.wav', 'alert_sound.ogg']
                found_sound = False
                
                for fmt in sound_formats:
                    fmt_path = os.path.join(audio_dir, fmt)
                    if os.path.exists(fmt_path):
                        alert_sound_path = fmt_path
                        found_sound = True
                        break
                
                if found_sound:
                    self.log_message(f"播放音频: {alert_sound_path}")
                    self.current_alert_sound = SoundLoader.load(alert_sound_path)
                    if self.current_alert_sound:
                        self.current_alert_sound.loop = True
                        self.current_alert_sound.play()
                        time.sleep(duration)
                        self.current_alert_sound.stop()
                else:
                    # 如果没有音频文件，使用系统提示音
                    self.log_message("未找到警报音频文件，使用系统提示音")
                    try:
                        # 在Android上使用系统声音
                        droid.playRingtone()
                        time.sleep(duration)
                        droid.stopRingtone()
                    except Exception as inner_e:
                        self.log_message(f"播放系统声音失败: {str(inner_e)}")
                        # 最后的备选方案 - 使用振动代替
                        self.vibrate(duration)
            else:
                # 在非Android环境下模拟
                self.log_message(f"模拟播放警报声音，持续 {duration} 秒")
                time.sleep(duration)
        except Exception as e:
            self.log_message(f"播放声音时出错: {str(e)}")
            
    def vibrate(self, duration=1):
        """控制设备震动"""
        try:
            if ANDROID_AVAILABLE:
                self.log_message(f"控制设备震动 {duration} 秒")
                droid.vibrate(duration * 1000)  # convert to ms
            else:
                self.log_message(f"模拟设备震动 {duration} 秒")
        except Exception as e:
            self.log_message(f"震动控制出错: {str(e)}")
            
    def flash_light(self, count=3, interval=0.5):
        """控制闪光灯闪烁"""
        try:
            if ANDROID_AVAILABLE:
                self.log_message(f"控制闪光灯闪烁 {count} 次")
                for i in range(count):
                    droid.toggleFlashLight(True)
                    time.sleep(interval)
                    droid.toggleFlashLight(False)
                    time.sleep(interval)
            else:
                self.log_message(f"模拟闪光灯闪烁 {count} 次")
        except Exception as e:
            self.log_message(f"闪光灯控制出错: {str(e)}")
            
    def show_notification(self, title, message):
        """显示通知"""
        try:
            if ANDROID_AVAILABLE:
                self.log_message(f"显示通知: {title} - {message}")
                droid.notify(title, message)
            else:
                self.log_message(f"模拟显示通知: {title} - {message}")
        except Exception as e:
            self.log_message(f"显示通知出错: {str(e)}")
            
    def show_floating_window(self, message="收到紧急警报，请立即处理！"):
        """显示悬浮窗提示"""
        try:
            if ANDROID_AVAILABLE:
                self.log_message(f"显示悬浮窗: {message}")
                # 在Android上使用通知作为悬浮窗的替代方案
                droid.notify("紧急警报", message, "ongoing_event")
            else:
                self.log_message(f"模拟显示悬浮窗: {message}")
        except Exception as e:
            self.log_message(f"显示悬浮窗出错: {str(e)}")
            
    def is_in_foreground(self):
        """检查应用是否在前台运行"""
        if ANDROID_AVAILABLE:
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                activity = PythonActivity.mActivity
                return activity.getWindow().getDecorView().getWindowVisibility() == 0  # VISIBLE
            except Exception as e:
                self.log_message(f"检查前台状态出错: {str(e)}")
                return True  # 默认假设在前台
        return True
            
    def start_alert(self, params=None):
        """启动综合警报
        
        Args:
            params: 可选参数字典，可包含alert_duration等配置
        """
        try:
            # 设置默认参数
            if params is None:
                params = {}
                
            self.is_alert_active = True
            self.log_message("启动综合警报")
            
            # 创建新的停止事件
            if hasattr(self, 'alert_stop_event'):
                self.alert_stop_event.set()
            self.alert_stop_event = threading.Event()
            
            # 更新UI
            if hasattr(self, 'status_label'):
                self.status_label.text = "警报中！"
                self.status_label.color = (1, 0, 0, 1)  # 红色
            
            # 记录警报来源
            self.alert_source = params.get('source', 'unknown')
            alert_message = params.get('message', '收到警报！')
            
            # 显示悬浮窗
            self.show_floating_window(alert_message)
            
            # 启动闪光灯线程
            if self.flash_thread is None or not self.flash_thread.is_alive():
                self.flash_thread = threading.Thread(target=self._flash_loop)
                self.flash_thread.daemon = True
                self.flash_thread.start()
            
            # 启动声音播放
            threading.Thread(target=self._sound_loop).start()
            
            # 震动
            self.vibrate()
            
            # 显示通知
            self.show_notification("紧急警报", alert_message)
            
            # 发送确认消息到服务端
            self.send_alert_ack()
            
        except Exception as e:
            self.log_message(f"启动警报出错: {str(e)}")
        
    def stop_alert(self, instance=None):
        """停止警报"""
        try:
            if self.is_alert_active:
                self.log_message("停止警报")
                
                # 设置停止事件
                self.alert_stop_event.set()
                self.is_alert_active = False
                
                # 停止音频播放
                if hasattr(self, 'current_alert_sound') and self.current_alert_sound:
                    try:
                        self.current_alert_sound.stop()
                    except Exception as e:
                        self.log_message(f"停止音频播放出错: {str(e)}")
                    self.current_alert_sound = None
                
                # 停止闪光灯
                if ANDROID_AVAILABLE:
                    try:
                        droid.toggleFlashLight(False)
                    except:
                        pass
                
                # 停止声音
                if ANDROID_AVAILABLE:
                    try:
                        droid.stopRingtone()
                    except:
                        pass
                
                # 停止震动
                if ANDROID_AVAILABLE:
                    try:
                        droid.cancelVibrate()
                    except Exception as e:
                        self.log_message(f"停止震动出错: {str(e)}")
                
                # 取消通知
                if ANDROID_AVAILABLE:
                    try:
                        droid.cancelNotification()
                    except:
                        pass
                
                # 更新UI
                if hasattr(self, 'status_label'):
                    self.status_label.text = "警报已停止"
                    self.status_label.color = (0, 1, 0, 1)  # 绿色
                
                # 移除悬浮窗
                if hasattr(self, 'floating_window') and self.floating_window and ANDROID_AVAILABLE:
                    try:
                        from jnius import autoclass, cast
                        Context = autoclass('android.content.Context')
                        WindowManager = autoclass('android.view.WindowManager')
                        PythonActivity = autoclass('org.kivy.android.PythonActivity')
                        activity = PythonActivity.mActivity
                        window_manager = cast(WindowManager, activity.getSystemService(Context.WINDOW_SERVICE))
                        window_manager.removeViewImmediate(self.floating_window)
                        self.floating_window = None
                    except Exception as e:
                        self.log_message(f"移除悬浮窗出错: {str(e)}")
                
                # 发送停止确认消息到服务端
                self.send_stop_alert_ack()
                
                self.log_message("警报已停止")
            else:
                self.log_message("没有活动的警报")
        except Exception as e:
            self.log_message(f"停止警报出错: {str(e)}")
            
    def _flash_loop(self):
        """闪光灯循环闪烁"""
        try:
            while not self.alert_stop_event.is_set() and self.is_alert_active:
                if ANDROID_AVAILABLE:
                    try:
                        droid.toggleFlashLight(True)
                        time.sleep(0.5)
                        droid.toggleFlashLight(False)
                        time.sleep(0.5)
                    except:
                        break
                else:
                    self.log_message("模拟闪光灯闪烁")
                    time.sleep(1)
        except Exception as e:
            self.log_message(f"闪光灯循环出错: {str(e)}")
            
    def _sound_loop(self):
        """声音循环播放"""
        try:
            while not self.alert_stop_event.is_set() and self.is_alert_active:
                self.play_sound(duration=2)
                if self.alert_stop_event.is_set():
                    break
                time.sleep(0.5)  # 短暂暂停后继续
        except Exception as e:
            self.log_message(f"声音循环出错: {str(e)}")

if __name__ == '__main__':
    try:
        print("正在初始化 Kivy 应用...")
        app = AlertClientApp()
        print("应用初始化完成，正在启动...")
        app.run()
    except Exception as e:
        import traceback
        print(f"应用程序启动失败: {str(e)}")
        print("详细错误信息:")
        traceback.print_exc()
        input("按回车键退出...")
    finally:
        print("程序已退出")
        input("按回车键关闭窗口...")