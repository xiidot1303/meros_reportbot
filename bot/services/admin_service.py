"""Who may run the admin-only bot commands.

The list is `ADMIN_USER_IDS` in `.env` — Telegram user ids, comma-separated.
Kept separate from `bot.services.access_service`, which answers a different
question (which *client cabinet* a phone number may open); this one is about
operating the bot itself and has no DB behind it.
"""

from config import ADMIN_USER_IDS


def is_admin(user_id):
    """True when this Telegram user id is in ADMIN_USER_IDS."""
    if not user_id:
        return False
    return int(user_id) in ADMIN_USER_IDS
