"""Verify .env and test TSETMC login."""

import sys
from pathlib import Path

# Allow running as script from project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import dotenv_values

from src.client import TsetmcClient, TsetmcAPIError
from src.config import validate_credentials
from src.schema import ERROR_BAD_CREDENTIALS, ERROR_CHANGE_PASSWORD


def main() -> int:
    print("بررسی فایل .env ...")
    env = dotenv_values(".env")
    required = ["TSETMC_USERNAME", "TSETMC_PASSWORD", "TSETMC_BASE_URL"]
    for key in required:
        val = env.get(key)
        if not val:
            print(f"  ✗ {key} خالی است")
            return 1
        print(f"  ✓ {key} = {val if key != 'TSETMC_PASSWORD' else '(مخفی، طول ' + str(len(val)) + ')'}")

    try:
        validate_credentials()
    except ValueError as e:
        print(f"خطا: {e}")
        return 1

    print("\nتست ورود به api.tsetmc.com ...")
    try:
        client = TsetmcClient()
        token = client.login()
        print(f"  ✓ ورود موفق (توکن: {len(token)} کاراکتر)")
        return 0
    except TsetmcAPIError as e:
        print(f"  ✗ {e}")
        if e.code == ERROR_BAD_CREDENTIALS:
            print("\nراهنما:")
            print("  - یوزر/پسورد را از TSETMC دوباره چک کنید")
            print("  - اگر حساب مسدود است با پشتیبانی تماس بگیرید (داخلی 482)")
        elif e.code in ERROR_CHANGE_PASSWORD:
            print("\nراهنما:")
            print("  - رمز اولین بار باید تغییر کند:")
            print("    python scripts/change_password.py رمز_جدید")
        return 1


if __name__ == "__main__":
    sys.exit(main())
