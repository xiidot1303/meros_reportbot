from bot.bot import *
from bot.models import Cabinet
from bot.services.feedback_notifier import (
    mark_admin_message_answered,
    send_answer_to_client,
)
from bot.services.feedback_service import (
    create_feedback,
    find_client_order,
    get_feedback_by_admin_message,
    has_marker,
    save_answer,
    search_client_orders,
    strip_marker,
)
from app.utils import format_number
from config import ADMIN_GROUP_ID


ADMIN_REPLY_SENT = "✅ Ответ отправлен клиенту."
ADMIN_REPLY_NO_USER = "⚠️ Не удалось отправить ответ: клиент недоступен."

# the client sends one of these along with their feedback
CLIENT_ATTACHMENTS = ("photo", "video", "document", "audio", "voice", "animation")


def _extract_attachment(message):
    """Return (file_id, file_type) for whatever media the admin attached."""
    if message.photo:
        return message.photo[-1].file_id, "photo"
    for attr in ("video", "document", "audio", "voice", "animation", "video_note", "sticker"):
        media = getattr(message, attr, None)
        if media:
            return media.file_id, attr
    return None, None


###############################################################################
# client side — the feedback conversation
###############################################################################


async def _ask_ttn(update: Update, context: CustomContext):
    """Entry point: ask for the ТТН number, offering the inline order search."""
    if update.callback_query:
        await update.callback_query.edit_message_reply_markup(None)

    context.user_data.pop("feedback", None)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.feedback_ask_ttn,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text=context.words.feedback_search_ttn,
                switch_inline_query_current_chat="",
            )],
            [InlineKeyboardButton(
                text=context.words.main_menu,
                callback_data="main_menu",
            )],
        ]),
    )
    return GET_FEEDBACK_TTN


async def get_ttn(update: Update, context: CustomContext):
    """The client picked an order from the inline search, or typed a ТТН by hand."""
    ttn_number = (update.effective_message.text or "").strip()

    order = await sync_to_async(find_client_order)(update.effective_user.id, ttn_number)
    if not order:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=context.words.feedback_ttn_not_found,
            parse_mode=ParseMode.HTML,
        )
        return GET_FEEDBACK_TTN

    context.user_data["feedback"] = {"ttn_number": order.deal_id}

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.feedback_ask_text.format(ttn_number=order.deal_id),
        parse_mode=ParseMode.HTML,
    )
    return GET_FEEDBACK_TEXT


async def get_text(update: Update, context: CustomContext):
    """Store the feedback text, then ask for an optional file."""
    feedback = context.user_data.get("feedback")
    if not feedback:
        return await _ask_ttn(update, context)

    feedback["text"] = (update.effective_message.text or "").strip()

    skip = context.words.feedback_skip_file
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.feedback_ask_file.format(skip=skip),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(text=skip, callback_data="feedback_skip_file")],
        ]),
    )
    return GET_FEEDBACK_FILE


async def get_file(update: Update, context: CustomContext):
    """The client attached a file — send the feedback on."""
    file_id, file_type = _extract_attachment(update.effective_message)
    if not file_id:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=context.words.feedback_wrong_file,
            parse_mode=ParseMode.HTML,
        )
        return GET_FEEDBACK_FILE

    return await _submit(update, context, file_id=file_id, file_type=file_type)


async def skip_file(update: Update, context: CustomContext):
    """The client chose to send the feedback without a file."""
    await update.callback_query.edit_message_reply_markup(None)
    return await _submit(update, context)


async def _submit(update: Update, context: CustomContext, file_id=None, file_type=None):
    """Persist the feedback and hand it to the notifier (client + admin group)."""
    from bot.services.feedback_notifier import notify_new_feedback

    data = context.user_data.pop("feedback", None)
    if not data:
        return await _ask_ttn(update, context)

    feedback = await sync_to_async(create_feedback)(
        user_id=update.effective_user.id,
        ttn_number=data["ttn_number"],
        text=data.get("text") or "",
        file_id=file_id,
        file_type=file_type,
    )
    if not feedback:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=context.words.feedback_error,
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END

    await notify_new_feedback(feedback)
    await main_menu(update, context)
    return ConversationHandler.END


async def ttn_inline_query(update: Update, context: CustomContext):
    """Inline search over the client's archived ("A") orders, keyed on deal_id."""
    query = update.inline_query.query or ""
    orders = await sync_to_async(search_client_orders)(update.effective_user.id, query)

    if not orders:
        await update.inline_query.answer(
            [InlineQueryResultArticle(
                id=str(uuid4()),
                title=context.words.feedback_inline_no_orders,
                description=context.words.feedback_inline_no_orders_description,
                input_message_content=InputTextMessageContent(
                    context.words.feedback_inline_no_orders
                ),
            )],
            cache_time=0,
            is_personal=True,
        )
        return

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=context.words.feedback_inline_order.format(deal_id=order.deal_id),
            description=context.words.feedback_inline_order_description.format(
                total_amount=_amount(order.total_amount),
                deal_datetime=_datetime(order.deal_datetime),
            ),
            # the chosen result posts the deal_id back into the chat
            input_message_content=InputTextMessageContent(order.deal_id),
        )
        for order in orders
    ]
    await update.inline_query.answer(results, cache_time=0, is_personal=True)


def _amount(value):
    if value is None:
        return "—"
    return format_number(round(float(value)))


def _datetime(value):
    if not value:
        return "—"
    return value.strftime("%d.%m.%Y %H:%M")


###############################################################################
# admin side
###############################################################################

async def admin_group_reply(update: Update, context: CustomContext):
    """An admin replied to a feedback message in the admin group.

    Only replies whose text/caption contains the @@@ marker are treated as
    answers; anything else is ordinary group chatter and is ignored.
    """
    message = update.effective_message
    if not message or not message.reply_to_message:
        return
    if ADMIN_GROUP_ID and update.effective_chat.id != ADMIN_GROUP_ID:
        return

    raw_text = message.text or message.caption or ""
    if not has_marker(raw_text):
        return

    feedback = await sync_to_async(get_feedback_by_admin_message)(
        message.reply_to_message.message_id
    )
    if not feedback:
        return

    file_id, file_type = _extract_attachment(message)
    answer = strip_marker(raw_text)
    if not (answer or file_id):
        return

    admin = update.effective_user
    admin_name = " ".join(filter(None, [admin.first_name, admin.last_name])) or admin.username

    feedback = await sync_to_async(save_answer)(
        feedback=feedback,
        answer=answer,
        admin_user_id=admin.id,
        admin_name=admin_name,
        file_id=file_id,
        file_type=file_type,
    )

    delivered = await send_answer_to_client(feedback, context.bot)
    await mark_admin_message_answered(feedback, context.bot)

    await message.reply_text(ADMIN_REPLY_SENT if delivered else ADMIN_REPLY_NO_USER)
