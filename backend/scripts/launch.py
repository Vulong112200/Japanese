"""Mở N5 Hub bằng 1 click: chạy server nền nếu chưa chạy, rồi mở trình duyệt.

Shortcut Desktop/taskbar gọi: .venv/Scripts/pythonw.exe scripts/launch.py (không hiện console).
"""
import subprocess
import time
import urllib.request
import webbrowser
from pathlib import Path

URL = "http://127.0.0.1:8000"
BACKEND = Path(__file__).resolve().parent.parent
LOG = BACKEND.parent / "data" / "database" / "server.log"


def up() -> bool:
    try:
        urllib.request.urlopen(URL + "/", timeout=1)
        return True
    except Exception:
        return False


if not up():
    LOG.parent.mkdir(parents=True, exist_ok=True)
    log = open(LOG, "ab")
    subprocess.Popen(
        [str(BACKEND / ".venv" / "Scripts" / "python.exe"), "-X", "utf8", "-m", "hub", "serve"],
        cwd=BACKEND, stdout=log, stderr=log, stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
    )
    for _ in range(40):  # chờ tối đa ~20 giây
        if up():
            break
        time.sleep(0.5)

webbrowser.open(URL)
