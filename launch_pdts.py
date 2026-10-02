"""
PDTS Desktop Launcher
Opens PDTS in a native desktop window (no browser, no terminal).

Run with:  python launch_pdts.py
Or double-click PDTS.exe (after building with build_exe.py)
"""

import os
import sys
import threading
import time
import socket
import webview

# Import the Flask app
from app import app


def find_free_port(start=5000, end=5100):
    """Find an available port so we never clash with other apps."""
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port available in range 5000-5100")


def run_flask(port):
    """Run Flask in a background thread."""
    app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False, threaded=True)


def wait_for_server(port, timeout=15):
    """Wait until the Flask server is accepting connections."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return True
        except OSError:
            time.sleep(0.15)
    return False


if __name__ == '__main__':
    port = find_free_port()
    url = f'http://127.0.0.1:{port}'

    # Start Flask in a daemon thread
    flask_thread = threading.Thread(target=run_flask, args=(port,), daemon=True)
    flask_thread.start()

    if not wait_for_server(port):
        print("Failed to start the PDTS server. Exiting.")
        sys.exit(1)

    # Open the native desktop window
    window = webview.create_window(
        title='PDTS — Pre-Arrest Diversion Tracking System',
        url=url,
        width=1280,
        height=860,
        min_size=(1024, 700),
        resizable=True,
        confirm_close=False,
        text_select=True,
    )

    # Block until the window is closed
    webview.start(debug=False)