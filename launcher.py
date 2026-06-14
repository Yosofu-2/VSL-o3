"""
LitManager Launcher
Starts the backend server, waits for it to be ready, then launches the frontend.
"""
import subprocess
import sys
import time
import os
import http.client
from pathlib import Path


def is_server_ready(host="127.0.0.1", port=8000, timeout=60):
    """Wait for the backend server to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            conn = http.client.HTTPConnection(host, port, timeout=2)
            conn.request("GET", "/api/health")
            resp = conn.getresponse()
            if resp.status == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    base_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent

    server_exe = base_dir / "LitManagerServer.exe"
    app_exe = base_dir / "LitManager.exe"

    if not server_exe.exists():
        print(f"ERROR: Server executable not found: {server_exe}")
        input("Press Enter to exit...")
        sys.exit(1)

    if not app_exe.exists():
        print(f"ERROR: Application executable not found: {app_exe}")
        input("Press Enter to exit...")
        sys.exit(1)

    # Start backend server
    print("Starting LitManager backend server...")
    server_proc = subprocess.Popen(
        [str(server_exe)],
        cwd=str(base_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    )

    # Wait for server to be ready
    print("Waiting for server to start...")
    if not is_server_ready():
        print("ERROR: Backend server failed to start within 60 seconds.")
        server_proc.kill()
        input("Press Enter to exit...")
        sys.exit(1)

    print("Server is ready! Launching LitManager...")

    # Launch frontend
    app_proc = subprocess.Popen(
        [str(app_exe)],
        cwd=str(base_dir),
    )

    # Wait for frontend to close
    app_proc.wait()

    # Cleanup: stop backend server
    print("Shutting down backend server...")
    server_proc.terminate()
    try:
        server_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_proc.kill()

    print("LitManager closed.")


if __name__ == "__main__":
    main()
