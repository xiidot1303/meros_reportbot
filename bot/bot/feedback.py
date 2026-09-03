from bot.bot import *
from bot.models import Cabinet, Feedback
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


# the conversation collects these one step at a time, then _submit() drains them
FEEDBACK_KEYS = ("feedback_type", "feedback_number", "feedback_text")


def _clear_feedback(context: CustomContext):
    """Drop any half-finished feedback, so a new one starts clean."""
    for key in FEEDBACK_KEYS:
        context.user_data.pop(key, None)


async def _ask_type(update: Update, context: CustomContext):
    """Entry point: which department is the feedback about?

    The answer decides the reference number that follows — a ТТН for the
    warehouse, a счёт-фактура for accounting, none at all for anything else.
    """
    if update.callback_query:
        await update.callback_query.edit_message_reply_markup(None)

    _clear_feedback(context)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.feedback_type_prompt,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text=context.words.feedback_type_warehouse,
                callback_data=f"feedback_type_{Feedback.WAREHOUSE}",
            )],
            [InlineKeyboardButton(
                text=context.words.feedback_type_accounting,
                callback_data=f"feedback_type_{Feedback.ACCOUNTING}",
            )],
            [InlineKeyboardButton(
                text=context.words.feedback_type_other,
                callback_data=f"feedback_type_{Feedback.OTHER}",
            )],
            [InlineKeyboardButton(
                text=context.words.main_menu,
                callback_data="main_menu",
            )],
        ]),
    )
    return SELECT_FEEDBACK_TYPE


async def select_type(update: Update, context: CustomContext):
    """The client picked a feedback type."""
    await update.callback_query.edit_message_reply_markup(None)

    feedback_type = update.callback_query.data[len("feedback_type_"):]
    context.user_data["feedback_type"] = feedback_type

    if feedback_type == Feedback.OTHER:
        # nothing to reference — go straight to the text
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=context.words.feedback_ask_text_other,
            parse_mode=ParseMode.HTML,
        )
        return GET_FEEDBACK_TEXT

    return await _ask_number(update, context, feedback_type)


# The inline query arrives as its own update, outside the conversation, so the
# feedback type travels in the query text itself rather than through shared
# state: the search button pre-fills this prefix and the handler reads it back.
ACCOUNTING_QUERY_PREFIX = "f:"


async def _ask_number(update: Update, context: CustomContext, feedback_type):
    """Ask for the ТТН / счёт-фактура, offering the inline order search.

    Warehouse searches orders by ТТН; accounting searches — and sends back —
    the order's `deal_id`, which is the factura number.
    """
    accounting = feedback_type == Feedback.ACCOUNTING
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(context.words.feedback_ask_factura if accounting
              else context.words.feedback_ask_ttn),
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                text=(context.words.feedback_search_factura if accounting
                      else context.words.feedback_search_ttn),
                switch_inline_query_current_chat=(
                    ACCOUNTING_QUERY_PREFIX if accounting else ""),
            )],
            [InlineKeyboardButton(
                text=context.words.main_menu,
                callback_data="main_menu",
            )],
        ]),
    )
    return GET_FEEDBACK_TTN


async def get_ttn(update: Update, context: CustomContext):
    """The client picked an order from the inline search, or typed a number by hand."""
    feedback_type = context.user_data.get("feedback_type")
    if not feedback_type:
        return await _ask_type(update, context)

    accounting = feedback_type == Feedback.ACCOUNTING
    number = (update.effective_message.text or "").strip()
    order = await find_client_order(
        update.effective_user.id, number, by_deal_id=accounting)
    if not order:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(context.words.feedback_factura_not_found if accounting
                  else context.words.feedback_ttn_not_found),
            parse_mode=ParseMode.HTML,
        )
        return GET_FEEDBACK_TTN

    number = order.deal_id if accounting else order.delivery_number
    context.user_data["feedback_number"] = number

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.feedback_ask_text.format(
            label=_number_label(context, feedback_type),
            number=number,
        ),
        parse_mode=ParseMode.HTML,
    )
    return GET_FEEDBACK_TEXT


def _number_label(context: CustomContext, feedback_type):
    """The client-facing name of the reference number for this feedback type."""
    if feedback_type == Feedback.ACCOUNTING:
        return context.words.feedback_number_label_factura
    return context.words.feedback_number_label_ttn


async def get_text(update: Update, context: CustomContext):
    """Store the feedback text, then ask for an optional file."""
    if not context.user_data.get("feedback_type"):
        return await _ask_type(update, context)

    context.user_data["feedback_text"] = (
        update.effective_message.text or "").strip()

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

    feedback_type = context.user_data.get("feedback_type")
    if not feedback_type:
        return await _ask_type(update, context)

    number = context.user_data.get("feedback_number") or ""
    text = context.user_data.get("feedback_text") or ""
    _clear_feedback(context)

    feedback = await create_feedback(
        user_id=update.effective_user.id,
        feedback_type=feedback_type,
        ttn_number=number,
        text=text,
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
    """Inline search over the client's archived ("A") orders.

    Keyed on the ТТН for a warehouse feedback and on the счёт-фактура number
    (the order's `deal_id`) for an accounting one — the same number the client
    is being asked for, so what they type matches what they see and send.
    """
    query = update.inline_query.query or ""
    accounting = query.startswith(ACCOUNTING_QUERY_PREFIX)
    if accounting:
        query = query[len(ACCOUNTING_QUERY_PREFIX):].strip()

    orders = await search_client_orders(
        update.effective_user.id, query, by_deal_id=accounting)

    if not orders:
        empty = (context.words.feedback_inline_no_facturas if accounting
                 else context.words.feedback_inline_no_orders)
        await update.inline_query.answer(
            [InlineQueryResultArticle(
                id=str(uuid4()),
                title=empty,
                description=(
                    context.words.feedback_inline_no_facturas_description
                    if accounting else
                    context.words.feedback_inline_no_orders_description
                ),
                input_message_content=InputTextMessageContent(empty),
            )],
            cache_time=0,
            is_personal=True,
        )
        return

    results = [
        InlineQueryResultArticle(
            id=str(uuid4()),
            title=(
                context.words.feedback_inline_factura.format(
                    deal_id=order.deal_id)
                if accounting else
                context.words.feedback_inline_order.format(
                    ttn_number=order.delivery_number)
            ),
            description=(
                context.words.feedback_inline_factura_description.format(
                    # the ТТН only exists once the warehouse has shipped, so
                    # for most facturas there is nothing to show here yet
                    ttn_number=order.delivery_number or "—",
                    total_amount=_amount(order.total_amount),
                )
                if accounting else
                context.words.feedback_inline_order_description.format(
                    total_amount=_amount(order.total_amount),
                    delivery_date=_date(order.delivery_date),
                )
            ),
            # the chosen result posts the reference number back into the chat
            input_message_content=InputTextMessageContent(
                order.deal_id if accounting else order.delivery_number),
        )
        for order in orders
    ]
    await update.inline_query.answer(results, cache_time=0, is_personal=True)


def _amount(value):
    if value is None:
        return "—"
    return format_number(round(float(value)))


def _date(value):
    if not value:
        return "—"
    return value.strftime("%d.%m.%Y")


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

    feedback = await get_feedback_by_admin_message(
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

    feedback = await save_answer(
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
