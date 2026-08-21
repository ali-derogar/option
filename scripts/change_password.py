"""Change TSETMC password (required on first login sometimes)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.client import TsetmcClient, TsetmcAPIError


def main() -> int:
    if len(sys.argv) < 2:
        print("استفاده: python scripts/change_password.py رمز_جدید")
        return 1

    new_password = sys.argv[1]
    if len(new_password) < 8:
        print("رمز جدید باید حداقل ۸ کاراکتر باشد.")
        return 1

    try:
        client = TsetmcClient()
        client.change_password(new_password)
        print("رمز با موفقیت تغییر کرد.")
        print("رمز جدید را در .env به‌روز کنید:")
        print(f"  TSETMC_PASSWORD='{new_password}'")
        return 0
    except TsetmcAPIError as e:
        print(f"خطا: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
