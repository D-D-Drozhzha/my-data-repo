# /// script
# requires-python = ">=3.11"
# dependencies = ["garminconnect>=0.3.20"]
# ///
"""One-time Garmin Connect login. Run it yourself in Terminal:

    uv run ~/garmin-mcp/garmin_login.py

It asks for your Garmin email, password (hidden) and 2FA code if enabled, then saves
session tokens to ~/.garminconnect (owner-only permissions). The password is not stored.
The MCP server only uses those tokens. Re-run if the server reports it is not logged in.
"""

import getpass
import os
import sys

from garminconnect import Garmin, GarminConnectTooManyRequestsError

TOKENSTORE = os.path.expanduser(os.getenv("GARMINTOKENS", "~/.garminconnect"))


def main() -> None:
    # Already logged in?
    if "--force" not in sys.argv:
        try:
            g = Garmin()
            g.login(TOKENSTORE)
            print(f"✅ Уже вошли как {g.get_full_name() or g.display_name}. Токены: {TOKENSTORE}")
            print("   (запустите с --force, чтобы войти заново)")
            return
        except Exception:
            pass

    email = input("Garmin email: ").strip()
    password = getpass.getpass("Garmin пароль (не отображается): ")
    g = Garmin(email, password, prompt_mfa=lambda: input("Код 2FA из письма/приложения: ").strip())
    try:
        g.login(TOKENSTORE)
    except GarminConnectTooManyRequestsError:
        print("❌ Garmin временно ограничил попытки входа. Подождите 15–30 минут и попробуйте снова.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Не удалось войти: {e}")
        sys.exit(1)
    print(f"✅ Готово: {g.get_full_name() or g.display_name}. Токены сохранены в {TOKENSTORE}")
    print("   Теперь перезапустите Claude Desktop.")


if __name__ == "__main__":
    main()
