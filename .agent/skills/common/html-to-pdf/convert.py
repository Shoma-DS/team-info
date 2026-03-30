#!/usr/bin/env python3
"""
HTML to PDF converter using headless Google Chrome.
Usage: python3 convert.py <input.html> [output.pdf]
"""

import sys
import subprocess
import os
import pathlib
import http.server
import threading
import socket
import time


def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def start_local_server(directory, port):
    """Start a simple HTTP server to serve local files (needed for web fonts)."""
    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None  # suppress logs
    httpd = http.server.HTTPServer(('localhost', port), handler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.daemon = True
    thread.start()
    return httpd


def get_chrome_path():
    if sys.platform == 'darwin':
        return '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    elif sys.platform == 'win32':
        paths = [
            r'C:\Program Files\Google\Chrome\Application\chrome.exe',
            r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        ]
        for p in paths:
            if os.path.exists(p):
                return p
    else:
        for cmd in ['google-chrome', 'chromium-browser', 'chromium']:
            result = subprocess.run(['which', cmd], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
    return None


def convert(input_html: str, output_pdf: str | None = None) -> str:
    input_path = pathlib.Path(input_html).resolve()
    if not input_path.exists():
        print(f"Error: {input_path} が見つかりません")
        sys.exit(1)

    if output_pdf is None:
        output_pdf = str(input_path.with_suffix('.pdf'))
    output_path = pathlib.Path(output_pdf).resolve()

    chrome = get_chrome_path()
    if not chrome:
        print("Error: Google Chrome が見つかりません")
        sys.exit(1)

    # Start local server so web fonts load correctly
    port = find_free_port()
    httpd = start_local_server(str(input_path.parent), port)
    time.sleep(0.3)  # wait for server to start

    url = f'http://localhost:{port}/{input_path.name}'

    cmd = [
        chrome,
        '--headless=new',
        '--no-sandbox',
        '--disable-gpu',
        '--run-all-compositor-stages-before-draw',
        '--virtual-time-budget=5000',
        f'--print-to-pdf={output_path}',
        '--print-to-pdf-no-header',
        '--no-pdf-header-footer',
        url,
    ]

    print(f"変換中: {input_path.name} → {output_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    httpd.shutdown()

    if output_path.exists():
        size_kb = output_path.stat().st_size // 1024
        print(f"✅ 完了: {output_path}  ({size_kb} KB)")
        return str(output_path)
    else:
        print(f"❌ 変換失敗")
        if result.stderr:
            print(result.stderr[:500])
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("使い方: python3 convert.py <input.html> [output.pdf]")
        sys.exit(1)

    input_html = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) >= 3 else None
    convert(input_html, output_pdf)
