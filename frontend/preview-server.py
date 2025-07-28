#!/usr/bin/env python3
import http.server
import socketserver
import os
import sys

# 切换到dist目录
try:
    os.chdir('dist')
    print("Changed to dist directory")
except:
    print("Error: dist directory not found. Please run 'npm run build' first.")
    sys.exit(1)

PORT = 3000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()
    
    def do_GET(self):
        # 处理SPA路由，将所有路由重定向到index.html
        if self.path != '/' and not self.path.startswith('/assets/') and not self.path.endswith('.ico'):
            self.path = '/index.html'
        return super().do_GET()

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"Frontend preview server at http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        sys.exit(0)
