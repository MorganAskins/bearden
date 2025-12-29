#!/usr/bin/env python3
"""Server management script for bearden dashboard.

Usage:
    uv run server.py start   - Start the server as a daemon
    uv run server.py stop    - Stop the running server
    uv run server.py restart - Restart the server
    uv run server.py status  - Check if the server is running
"""

import os
import signal
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
PID_FILE = BASE_DIR / "gunicorn.pid"
CONFIG_FILE = BASE_DIR / "gunicorn.conf.py"


def get_pid() -> int | None:
    """Read the PID from the PID file."""
    if not PID_FILE.exists():
        return None
    try:
        pid = int(PID_FILE.read_text().strip())
        # Check if process is actually running
        os.kill(pid, 0)
        return pid
    except (ValueError, ProcessLookupError, PermissionError):
        # Stale PID file
        PID_FILE.unlink(missing_ok=True)
        return None


def start() -> int:
    """Start the gunicorn server as a daemon."""
    pid = get_pid()
    if pid:
        print(f"Server already running (PID: {pid})")
        return 1

    cmd = [
        "uv",
        "run",
        "gunicorn",
        "--config",
        str(CONFIG_FILE),
        "--daemon",
        "--pid",
        str(PID_FILE),
        "wsgi:application",
    ]

    result = subprocess.run(cmd, cwd=BASE_DIR)
    if result.returncode == 0:
        # Wait briefly for PID file to be written
        import time

        time.sleep(0.5)
        pid = get_pid()
        if pid:
            print(f"Server started (PID: {pid})")
            return 0
        else:
            print("Server started but PID file not found")
            return 1
    else:
        print("Failed to start server")
        return result.returncode


def stop() -> int:
    """Stop the gunicorn server gracefully."""
    pid = get_pid()
    if not pid:
        print("Server is not running")
        return 1

    try:
        # Send SIGTERM for graceful shutdown
        os.kill(pid, signal.SIGTERM)
        print(f"Stopping server (PID: {pid})...")

        # Wait for process to terminate
        import time

        for _ in range(30):  # Wait up to 30 seconds
            time.sleep(1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                PID_FILE.unlink(missing_ok=True)
                print("Server stopped")
                return 0

        # Force kill if still running
        print("Server did not stop gracefully, forcing...")
        os.kill(pid, signal.SIGKILL)
        PID_FILE.unlink(missing_ok=True)
        print("Server killed")
        return 0
    except ProcessLookupError:
        PID_FILE.unlink(missing_ok=True)
        print("Server was not running")
        return 0


def restart() -> int:
    """Restart the gunicorn server."""
    pid = get_pid()
    if pid:
        stop()
    return start()


def status() -> int:
    """Check if the server is running."""
    pid = get_pid()
    if pid:
        print(f"Server is running (PID: {pid})")
        return 0
    else:
        print("Server is not running")
        return 1


def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    command = sys.argv[1].lower()

    commands = {
        "start": start,
        "stop": stop,
        "restart": restart,
        "status": status,
    }

    if command not in commands:
        print(f"Unknown command: {command}")
        print(__doc__)
        return 1

    return commands[command]()


if __name__ == "__main__":
    sys.exit(main())
