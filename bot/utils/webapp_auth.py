import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from config import BOT_API_TOKEN


MAX_AUTH_AGE = 24 * 60 * 60


def verify_init_data(init_data, max_age=MAX_AUTH_AGE):
    """Validate a Telegram WebApp initData string against the bot token.

    Returns the parsed user dict on success, otherwise None.
    See https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not init_data:
        return None

    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(
        f"{key}={parsed[key]}" for key in sorted(parsed)
    )
    secret_key = hmac.new(b"WebAppData", BOT_API_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        return None

    auth_date = parsed.get("auth_date")
    if max_age and auth_date:
        try:
            if time.time() - int(auth_date) > max_age:
                return None
        except ValueError:
            return None

    try:
        return json.loads(parsed.get("user", "{}")) or None
    except ValueError:
        return None
