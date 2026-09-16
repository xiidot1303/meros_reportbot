import asyncio
from dataclasses import dataclass
from telegram.ext import (
    Application,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    ExtBot,
    TypeHandler,
    PicklePersistence
)
from telegram import Update
from config import BOT_API_TOKEN, WEBHOOK_URL
from bot.control.handlers import handlers
from bot.control.commands import set_bot_commands
from bot.bot.main import error_handler
from bot import *
from python_telegram_bot_django_persistence.persistence import DjangoPersistence


persistence = PicklePersistence(filepath="persistencebot")
context_types = ContextTypes(context=CustomContext)
application = Application.builder().token(
    BOT_API_TOKEN).context_types(context_types).persistence(DjangoPersistence()).build()

# add handlers
for handler in handlers[::-1]:
    application.add_handler(handler)

application.add_error_handler(error_handler)

# `post_init` is only honoured by run_polling/run_webhook, and production runs
# neither (run_uvicorn drives the Application directly), so the command menu is
# published from `on_startup` below, which both entry points do reach.
application.post_init = set_bot_commands


async def on_startup():
    """Everything that must happen once the Application is running.

    Called by both `run_uvicorn` (production) and `run_polling` (dev). Kept
    separate from `post_init` because that hook never fires on the uvicorn
    path — see the note above.
    """
    await set_bot_commands(application)


# webhook functions

async def set_webhook():
    await application.bot.set_webhook(
        url=f"{WEBHOOK_URL}/webhook",
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


async def delete_webhook():
    await application.bot.delete_webhook()
