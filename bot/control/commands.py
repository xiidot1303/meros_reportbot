"""What appears in Telegram's command menu, and for whom.

Telegram scopes the menu per chat, so the admin-only commands are published
twice: an empty-but-for-/start default list for everybody, and a longer list
set individually for each id in `ADMIN_USER_IDS`. That is only *visibility* —
a non-admin who types `/update_phones` anyway still hits the `is_admin` guard
in [bot/bot/admin_phones.py](bot/bot/admin_phones.py), which is what actually
denies them.

Called once on startup from [bot/control/updater.py](bot/control/updater.py).
"""

import logging

from telegram import BotCommand, BotCommandScopeChat, BotCommandScopeDefault

from config import ADMIN_USER_IDS


logger = logging.getLogger(__name__)


# Shown to every user.
DEFAULT_COMMANDS = [
    BotCommand("start", "Главное меню / Asosiy menyu"),
]

# Appended for admins only.
ADMIN_COMMANDS = DEFAULT_COMMANDS + [
    BotCommand("update_phones", "Обновить номера телефонов из Excel"),
]


async def set_bot_commands(application):
    """Publish both command lists. Never raises — a failure here must not
    stop the bot from starting, since the commands still work when typed."""
    try:
        await application.bot.set_my_commands(
            DEFAULT_COMMANDS, scope=BotCommandScopeDefault())
    except Exception:
        logger.warning("Failed to set default bot commands", exc_info=True)

    for user_id in ADMIN_USER_IDS:
        try:
            await application.bot.set_my_commands(
                ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=user_id))
        except Exception:
            # most likely the admin has never opened a chat with the bot
            logger.warning(
                "Failed to set admin bot commands for %s", user_id, exc_info=True)
