import socket
import threading
import json
from kivy.clock import Clock

class NetworkManager:
    def __init__(self, callback=None):
        """
        初始化网络管理器
        
        Args:
            callback: 接收消息时的回调函数
        """
        self.callback = callback
        self.socket = None
        self.is_listening = False
        self.connection_thread = None
        self.client_handlers = []
    
    def start_server(self, host='0.0.0.0', port=8888):
        """
        启动服务器监听
        
        Args:
            host: 监听地址
            port: 监听端口
            
        Returns:
            bool: 是否成功启动
        """
        try:
            # 创建套接字
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((host, port))
            self.socket.listen(5)
            
            self.is_listening = True
            
            # 在新线程中接受连接
            self.connection_thread = threading.Thread(target=self.accept_connections)
            self.connection_thread.daemon = True
            self.connection_thread.start()
            
            return True
        except Exception as e:
            if self.callback:
                self.callback({"type": "error", "message": f"启动服务失败: {str(e)}"})
            return False
    
    def stop_server(self):
        """停止服务器"""
        if self.socket:
            self.is_listening = False
            self.socket.close()
            self.socket = None
            
            # 清理客户端处理线程
            self.client_handlers = []
            
            if self.callback:
                self.callback({"type": "info", "message": "服务已停止"})
    
    def accept_connections(self):
        """接受客户端连接"""
        while self.is_listening:
            try:
                client_socket, address = self.socket.accept()
                
                # 创建客户端处理线程
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
                
                # 保存线程引用
                self.client_handlers.append(client_thread)
                
                if self.callback:
                    self.callback({
                        "type": "connection", 
                        "message": f"接受来自 {address[0]}:{address[1]} 的连接"
                    })
            except:
                # 如果socket被关闭，退出循环
                break
    
    def handle_client(self, client_socket, address):
        """
        处理客户端连接
        
        Args:
            client_socket: 客户端套接字
            address: 客户端地址
        """
        try:
            while self.is_listening:
                data = client_socket.recv(1024)
                if not data:
                    break
                
                # 处理接收到的数据
                try:
                    # 尝试解析JSON数据
                    message = json.loads(data.decode('utf-8'))
                    
                    # 添加来源信息
                    message['source'] = {
                        'ip': address[0],
                        'port': address[1]
                    }
                    
                    # 回调通知
                    if self.callback:
                        self.callback(message)
                    
                    # 发送响应
                    response = {'status': 'ok', 'message': '已处理'}
                    client_socket.send(json.dumps(response).encode('utf-8'))
                    
                except json.JSONDecodeError:
                    # 非JSON格式数据处理
                    text_data = data.decode('utf-8', errors='ignore')
                    if self.callback:
                        self.callback({
                            "type": "raw_data",
                            "message": text_data,
                            "source": {
                                'ip': address[0],
                                'port': address[1]
                            }
                        })
                except Exception as e:
                    if self.callback:
                        self.callback({
                            "type": "error",
                            "message": f"处理数据时出错: {str(e)}",
                            "source": {
                                'ip': address[0],
                                'port': address[1]
                            }
                        })
        except:
            pass
        finally:
            client_socket.close()
            if self.callback:
                self.callback({
                    "type": "disconnection",
                    "message": f"客户端 {address[0]}:{address[1]} 已断开连接"
                })
    
    def send_message(self, host, port, message):
        """
        向指定主机发送消息
        
        Args:
            host: 目标主机地址
            port: 目标主机端口
            message: 要发送的消息(字典)
            
        Returns:
            dict: 响应消息
        """
        try:
            # 创建临时套接字
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5)  # 设置超时
            client_socket.connect((host, port))
            
            # 发送消息
            client_socket.send(json.dumps(message).encode('utf-8'))
            
            # 接收响应
            response_data = client_socket.recv(1024)
            response = json.loads(response_data.decode('utf-8'))
            
            client_socket.close()
            return response
        except Exception as e:
            return {"status": "error", "message": str(e)}