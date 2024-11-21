from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket
import webbrowser

def get_local_ip():
    try:
        # 获取本机IP地址
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def run_server(port=8000):
    # 获取本地IP
    local_ip = get_local_ip()
    
    # 创建服务器
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHTTPRequestHandler)
    
    print(f"服务器已启动:")
    print(f"本地访问: http://localhost:{port}")
    print(f"局域网访问: http://{local_ip}:{port}")
    print("按 Ctrl+C 停止服务器")
    
    # 自动在浏览器中打开
    webbrowser.open(f"http://localhost:{port}")
    
    # 启动服务器
    httpd.serve_forever()

if __name__ == "__main__":
    run_server() 