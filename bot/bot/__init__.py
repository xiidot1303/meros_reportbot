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
from bot.services.redis_service import get_user_lang


async def is_message_back(update: Update):
    if update.message.text == Strings(update.effective_user.id).back:
        return True
    else:
        return False


async def main_menu(update: Update, context: CustomContext):
    bot = context.bot
    lang = await sync_to_async(get_user_lang)(update.effective_user.id)
    lang_code = "ru" if lang == 1 else "uz"

    inline_keyboards = [
        [InlineKeyboardButton(text=context.words.reconciliation_act, callback_data="reconciliation_act")],
        [InlineKeyboardButton(text=context.words.order_history, callback_data="order_history")],
        [InlineKeyboardButton(text=context.words.client_debts, callback_data="client_debts")],
        [InlineKeyboardButton(text=context.words.facturas, callback_data="facturas")],
        [InlineKeyboardButton(text=context.words.switch_cabinet, callback_data="switch_cabinet")],
        [InlineKeyboardButton(
            text=context.words.feedback,
            web_app=WebAppInfo(url=f"{WEBAPP_URL}/webapp/feedback/?lang={lang_code}"),
        )],
    ]
    if update.callback_query:
        if update.effective_message.text:
            await update.callback_query.edit_message_text(
                context.words.main_menu,
                reply_markup=InlineKeyboardMarkup(inline_keyboards),
            )
            return ConversationHandler.END
        else:
            await update.callback_query.edit_message_reply_markup()
    await bot.send_message(
        update.effective_chat.id,
        context.words.main_menu,
        reply_markup=InlineKeyboardMarkup(inline_keyboards),
    )

    return ConversationHandler.END