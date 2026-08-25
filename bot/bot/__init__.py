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
from bot.services.redis_service import get_user_lang


async def is_message_back(update: Update):
    if update.message.text == Strings(update.effective_user.id).back:
        return True
    else:
        return False


async def _is_owner_of_active_cabinet(update: Update) -> bool:
    """Whether the user owns the client currently open, and so may manage its staff."""
    from bot.services.access_service import is_owner_async
    from bot.models import Bot_user, Cabinet
    try:
        bot_user = await Bot_user.objects.aget(user_id=update.effective_user.id)
        cabinet = await bot_user.get_active_cabinet
        client = await cabinet.get_client()
    except Exception:
        return False
    return await is_owner_async(bot_user.phone, client)


async def main_menu(update: Update, context: CustomContext):
    bot = context.bot

    inline_keyboards = [
        [InlineKeyboardButton(text=context.words.reconciliation_act, callback_data="reconciliation_act")],
        [InlineKeyboardButton(text=context.words.order_history, callback_data="order_history")],
        [InlineKeyboardButton(text=context.words.client_debts, callback_data="client_debts")],
        [InlineKeyboardButton(text=context.words.facturas, callback_data="facturas")],
        [InlineKeyboardButton(text=context.words.switch_cabinet, callback_data="switch_cabinet")],
    ]
    # staff management belongs to the owner of the open client only
    if await _is_owner_of_active_cabinet(update):
        inline_keyboards.append(
            [InlineKeyboardButton(text=context.words.staff, callback_data="staff")]
        )
    inline_keyboards.append(
        [InlineKeyboardButton(text=context.words.feedback, callback_data="feedback")]
    )
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