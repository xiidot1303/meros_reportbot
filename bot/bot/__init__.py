from bot import *
from telegram import Update
from telegram.ext import ContextTypes, CallbackContext, ExtBot, Application
from dataclasses import dataclass
from asgiref.sync import sync_to_async
from bot.utils import *
from bot.utils.bot_functions import *
from bot.utils.keyboards import *
from bot.services import *
from bot.resources.conversationList import *
from app.services import filter_objects_sync
from config import WEBAPP_URL


async def is_message_back(update: Update):
    if update.message.text == Strings(update.effective_user.id).back:
        return True
    else:
        return False


async def main_menu(update: Update, context: CustomContext):
    bot = context.bot

    inline_keyboards = [
        [InlineKeyboardButton(text=context.words.reconciliation_act, callback_data="reconciliation_act")],
        [InlineKeyboardButton(text=context.words.switch_cabinet, callback_data="switch_cabinet")],
    ]
    if update.callback_query:
        await update.callback_query.edit_message_text(
            context.words.main_menu,
            reply_markup=InlineKeyboardMarkup(inline_keyboards),
        )
        return ConversationHandler.END
    await bot.send_message(
        update.message.chat_id,
        context.words.main_menu,
        reply_markup=InlineKeyboardMarkup(inline_keyboards),
    )

    return ConversationHandler.END