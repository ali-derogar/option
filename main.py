"""
TSETMC Options — single entry point (backend API + frontend UI).

Usage:
    python main.py
"""

from __future__ import annotations

import os
import sys
import threading
import time
import webbrowser

from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv("WEB_HOST", "0.0.0.0")
PORT = int(os.getenv("WEB_PORT", "8080"))
OPEN_BROWSER = os.getenv("WEB_OPEN_BROWSER", "1").strip().lower() in ("1", "true", "yes")


def _open_browser() -> None:
    time.sleep(1.2)
    url = f"http://127.0.0.1:{PORT}"
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main() -> None:
    from src.config import TSETMC_USERNAME, validate_credentials

    print("=" * 50)
    print("  TSETMC Options Dashboard")
    print("=" * 50)
    print(f"  Frontend + API: http://127.0.0.1:{PORT}")
    if HOST == "0.0.0.0":
        print(f"  Network:          http://localhost:{PORT}")
    print("-" * 50)

    if not TSETMC_USERNAME:
        print("  ⚠ TSETMC_USERNAME در .env تنظیم نشده — به‌روزرسانی داده کار نمی‌کند")
    else:
        try:
            validate_credentials()
            print("  ✓ اعتبارسنجی .env OK")
        except ValueError as exc:
            print(f"  ⚠ {exc}")

    print("-" * 50)
    print("  Ctrl+C برای توقف")
    print("=" * 50)

    if OPEN_BROWSER:
        threading.Thread(target=_open_browser, daemon=True).start()

    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=HOST,
        port=PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nمتوقف شد.")
        sys.exit(0)
