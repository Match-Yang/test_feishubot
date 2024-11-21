from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket
import webbrowser
import argparse
import os
import requests
import json

def send_to_feishu(webhook_url, message):
    """发送消息到飞书机器人"""
    headers = {
        'Content-Type': 'application/json'
    }
    payload = {
        "msg_type": "text",
        "content": {
            "text": message
        }
    }
    try:
        response = requests.post(webhook_url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print("消息已成功发送到飞书")
        else:
            print(f"发送失败，状态码：{response.status_code}")
    except Exception as e:
        print(f"发送失败：{str(e)}")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

class CustomHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, **kwargs):
        super().__init__(*args, directory=directory, **kwargs)

def run_server(port=8000, directory=None, webhook_url=None):
    local_ip = get_local_ip()
    
    if directory:
        os.chdir(directory)
        handler = lambda *args, **kwargs: CustomHandler(*args, directory=directory, **kwargs)
    else:
        handler = SimpleHTTPRequestHandler
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, handler)
    
    current_dir = os.path.abspath(directory if directory else '.')
    server_info = (
        f"\n文件服务器信息：\n"
        f"当前服务目录: {current_dir}\n"
        f"本地访问: http://localhost:{port}\n"
        f"局域网访问: http://{local_ip}:{port}"
    )
    
    print(server_info)
    print("\n按 Ctrl+C 停止服务器")
    
    # 如果提供了webhook地址，发送到飞书
    if webhook_url:
        send_to_feishu(webhook_url, server_info)
    
    webbrowser.open(f"http://localhost:{port}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='启动一个简单的HTTP文件服务器')
    parser.add_argument('-p', '--port', type=int, default=8000, help='指定端口号（默认：8000）')
    parser.add_argument('-d', '--directory', type=str, help='指定服务器根目录')
    parser.add_argument('-w', '--webhook', type=str, help='飞书机器人 Webhook 地址')
    
    args = parser.parse_args()
    run_server(args.port, args.directory, args.webhook) 