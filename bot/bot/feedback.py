from bot.bot import *
from bot.models import Cabinet, Feedback
from bot.services.feedback_notifier import (
    mark_admin_message_answered,
    mark_admin_message_in_progress,
    notify_client_in_review,
    send_answer_to_client,
)
from bot.services.feedback_service import (
    TAKE_CALLBACK_PREFIX,
    create_feedback,
    find_client_order,
    get_client_order,
    get_feedback_by_admin_message,
    has_marker,
    list_client_orders,
    save_answer,
    strip_marker,
    take_feedback,
)
from app.utils import format_number


ADMIN_REPLY_SENT = "✅ Ответ отправлен клиенту."
ADMIN_REPLY_NO_USER = "⚠️ Не удалось отправить ответ: клиент недоступен."
ADMIN_TAKEN = "✅ Обращение взято в работу, клиент уведомлён."
ADMIN_TAKEN_NO_USER = "✅ Обращение взято в работу. Клиент недоступен для уведомления."
ADMIN_ALREADY_TAKEN = "Обращение уже взял в работу: {admin}."
ADMIN_ALREADY_ANSWERED = "На это обращение уже ответили."
ADMIN_FEEDBACK_NOT_FOUND = "Обращение не найдено."

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


# callback data of the order picker
PICK_PREFIX = "feedback_pick_"
PAGE_PREFIX = "feedback_page_"
PAGE_NOOP = "feedback_page_noop"

# one picker button: the number being asked for, then amount and date so the
# client can tell orders apart
ORDER_BUTTON = "{icon} {number} | {amount} | {date}"


def _is_accounting(feedback_type):
    return feedback_type == Feedback.ACCOUNTING


async def _orders_keyboard(update: Update, context: CustomContext, feedback_type, page=0):
    """The picker for one page — or None when there is nothing to pick.

    Warehouse lists orders by ТТН; accounting by the order's `deal_id`, which
    is the счёт-фактура number.
    """
    accounting = _is_accounting(feedback_type)
    orders, page, page_count = await list_client_orders(
        update.effective_user.id, page, by_deal_id=accounting)
    if not orders:
        return None

    rows = [
        [InlineKeyboardButton(
            text=ORDER_BUTTON.format(
                icon="\U0001F4C4" if accounting else "\U0001F4E6",
                number=order.deal_id if accounting else order.delivery_number,
                amount=_amount(order.total_amount),
                date=_date(order.delivery_date),
            ),
            callback_data=f"{PICK_PREFIX}{order.pk}",
        )]
        for order in orders
    ]

    if page_count > 1:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(
                text="\u2B05\uFE0F", callback_data=f"{PAGE_PREFIX}{page - 1}"))
        nav.append(InlineKeyboardButton(
            text=f"{page + 1}/{page_count}", callback_data=PAGE_NOOP))
        if page < page_count - 1:
            nav.append(InlineKeyboardButton(
                text="\u27A1\uFE0F", callback_data=f"{PAGE_PREFIX}{page + 1}"))
        rows.append(nav)

    rows.append([
        # re-enters the conversation at the type choice
        InlineKeyboardButton(text=context.words.back, callback_data="feedback"),
        InlineKeyboardButton(text=context.words.main_menu, callback_data="main_menu"),
    ])
    return InlineKeyboardMarkup(rows)


async def _ask_number(update: Update, context: CustomContext, feedback_type):
    """Ask for the ТТН / счёт-фактура as a paged list of the client's orders.

    Typing the number by hand still works — `get_ttn` takes it.
    """
    accounting = _is_accounting(feedback_type)
    keyboard = await _orders_keyboard(update, context, feedback_type)
    if not keyboard:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(context.words.feedback_no_facturas if accounting
                  else context.words.feedback_no_orders),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(text=context.words.back, callback_data="feedback"),
                InlineKeyboardButton(text=context.words.main_menu, callback_data="main_menu"),
            ]]),
        )
        return GET_FEEDBACK_TTN

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(context.words.feedback_ask_factura if accounting
              else context.words.feedback_ask_ttn),
        parse_mode=ParseMode.HTML,
        reply_markup=keyboard,
    )
    return GET_FEEDBACK_TTN


async def change_page(update: Update, context: CustomContext):
    """⬅️ / ➡️ in the order picker — redraw the same message on another page."""
    query = update.callback_query
    if query.data == PAGE_NOOP:
        # the "2/5" counter between the arrows
        await query.answer()
        return GET_FEEDBACK_TTN

    feedback_type = context.user_data.get("feedback_type")
    if not feedback_type:
        return await _ask_type(update, context)

    await query.answer()
    keyboard = await _orders_keyboard(
        update, context, feedback_type, page=int(query.data[len(PAGE_PREFIX):]))
    if keyboard:
        await query.edit_message_reply_markup(keyboard)
    return GET_FEEDBACK_TTN


async def pick_order(update: Update, context: CustomContext):
    """The client tapped an order in the picker."""
    query = update.callback_query
    feedback_type = context.user_data.get("feedback_type")
    if not feedback_type:
        return await _ask_type(update, context)

    accounting = _is_accounting(feedback_type)
    order = await get_client_order(
        update.effective_user.id, int(query.data[len(PICK_PREFIX):]),
        by_deal_id=accounting)
    if not order:
        # e.g. the active cabinet was switched since the list was drawn
        await query.answer(
            context.words.feedback_factura_not_found if accounting
            else context.words.feedback_ttn_not_found,
            show_alert=True,
        )
        return GET_FEEDBACK_TTN

    await query.answer()
    await query.edit_message_reply_markup(None)
    return await _accept_order(update, context, feedback_type, order)


async def get_ttn(update: Update, context: CustomContext):
    """The client typed the ТТН / счёт-фактура number by hand."""
    feedback_type = context.user_data.get("feedback_type")
    if not feedback_type:
        return await _ask_type(update, context)

    accounting = _is_accounting(feedback_type)
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

    return await _accept_order(update, context, feedback_type, order)


async def _accept_order(update: Update, context: CustomContext, feedback_type, order):
    """Remember the order's number and move on to the feedback text."""
    number = order.deal_id if _is_accounting(feedback_type) else order.delivery_number
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

def _admin_name(user):
    return " ".join(filter(None, [user.first_name, user.last_name])) or user.username


async def admin_take(update: Update, context: CustomContext):
    """A staff member pressed "take" under a feedback in the admin group.

    The first click wins: the group message is rewritten to show who took it
    (which also drops the button) and the client is told it is under review.
    Later clicks only get a popup saying who has it.
    """
    query = update.callback_query
    feedback_id = int(query.data[len(TAKE_CALLBACK_PREFIX):])
    admin = update.effective_user

    feedback, taken = await take_feedback(
        feedback_id, update.effective_chat.id, admin.id, _admin_name(admin))

    if not feedback:
        await query.answer(ADMIN_FEEDBACK_NOT_FOUND, show_alert=True)
        return
    if not taken:
        await query.answer(
            ADMIN_ALREADY_ANSWERED if feedback.status == Feedback.ANSWERED
            else ADMIN_ALREADY_TAKEN.format(admin=feedback.taken_by_name or "—"),
            show_alert=True,
        )
        return

    await mark_admin_message_in_progress(feedback, context.bot)
    delivered = await notify_client_in_review(feedback, context.bot)
    await query.answer(ADMIN_TAKEN if delivered else ADMIN_TAKEN_NO_USER)


async def admin_group_reply(update: Update, context: CustomContext):
    """An admin replied to a feedback message in the admin group.

    Only replies whose text/caption contains the @@@ marker are treated as
    answers; anything else is ordinary group chatter and is ignored.
    """
    message = update.effective_message
    if not message or not message.reply_to_message:
        return

    raw_text = message.text or message.caption or ""
    if not has_marker(raw_text):
        return

    # the main admin group or a region group — whichever the feedback was
    # posted to; a reply anywhere else matches no feedback and is ignored
    feedback = await get_feedback_by_admin_message(
        update.effective_chat.id, message.reply_to_message.message_id
    )
    if not feedback:
        return

    file_id, file_type = _extract_attachment(message)
    answer = strip_marker(raw_text)
    if not (answer or file_id):
        return

    admin = update.effective_user

    feedback = await save_answer(
        feedback=feedback,
        answer=answer,
        admin_user_id=admin.id,
        admin_name=_admin_name(admin),
        file_id=file_id,
        file_type=file_type,
    )

    delivered = await send_answer_to_client(feedback, context.bot)
    await mark_admin_message_answered(feedback, context.bot)

    await message.reply_text(ADMIN_REPLY_SENT if delivered else ADMIN_REPLY_NO_USER)
