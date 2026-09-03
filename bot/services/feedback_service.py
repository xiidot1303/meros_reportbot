import html

from django.utils import timezone

from app.models import Order
from bot.models import Bot_user, Cabinet, Feedback


ADMIN_FEEDBACK_TEXT = """\U0001F4DD <b>Новое обращение от клиента</b>
<b>Тип:</b> {feedback_type}
{number_line}<b>Клиент:</b> {client}
<b>Телефон:</b> {phone}

<b>Обращение:</b>
{text}{attachment}"""

# omitted entirely for an "other" feedback, which carries no reference number
NUMBER_LINE = "<b>{label}:</b> <code>{number}</code>\n"

ATTACHMENT_NOTE = "\n\n\U0001F4CE К обращению приложен файл."

ANSWER_MARKER = "@@@"

# Telegram allows at most 50 inline results per answer
INLINE_RESULT_LIMIT = 50

ADMIN_ANSWERED_TEXT = """✅ <b>Обращение обработано</b>
<b>Тип:</b> {feedback_type}
{number_line}<b>Клиент:</b> {client}

<b>Обращение:</b>
{text}{attachment}

<b>Ответ ({admin}):</b>
{answer}"""


async def create_feedback(user_id, text, feedback_type=Feedback.WAREHOUSE,
                          ttn_number="", file_id=None, file_type=None):
    """Store a client's feedback. Returns the Feedback, or None if the user is unknown.

    `ttn_number` holds the ТТН for a warehouse feedback and the счёт-фактура
    number (the order's `deal_id`) for an accounting one; it is empty for
    "other", which references nothing.
    """
    bot_user = await Bot_user.objects.filter(user_id=user_id).afirst()
    if not bot_user:
        return None

    cabinet = await Cabinet.objects.filter(
        bot_user=bot_user, is_active=True
    ).select_related("client").afirst()

    return await Feedback.objects.acreate(
        bot_user=bot_user,
        client=cabinet.client if cabinet else None,
        feedback_type=feedback_type,
        ttn_number=ttn_number or "",
        text=text,
        file_id=file_id,
        file_type=file_type,
    )


async def search_client_orders(user_id, query="", limit=INLINE_RESULT_LIMIT,
                               by_deal_id=False):
    """Archived ("A") orders of the user's active cabinet, matched by number prefix.

    Feeds the inline-query search; returns [] when the user has no cabinet.
    `by_deal_id` matches on the счёт-фактура number (`deal_id`) instead of the
    ТТН, so the accounting flow searches by the same number it will send on.
    Prefix (not substring) matching, so a query must start the number — this is
    what lets the lookup use an index instead of scanning.

    Orders lacking the number being searched are skipped, since there would be
    nothing for the client to pick: an order gets its `deal_id` up front but
    its ТТН only once the warehouse ships it, so the two exclusions are not
    interchangeable — filtering the factura search on the ТТН would hide almost
    every order.
    """
    cabinet = await Cabinet.objects.filter(
        bot_user__user_id=user_id, is_active=True
    ).select_related("client").afirst()
    if not (cabinet and cabinet.client):
        return []

    field = "deal_id" if by_deal_id else "delivery_number"
    orders = Order.objects.filter(
        client=cabinet.client, status="A"
    ).exclude(**{f"{field}__isnull": True}).exclude(**{field: ""})
    query = (query or "").strip()
    if query:
        orders = orders.filter(**{f"{field}__istartswith": query})
    # sorted by the same date the picker shows, so newest-first reads correctly
    return [o async for o in orders.order_by("-delivery_date", "-id")[:limit]]


async def find_client_order(user_id, number, by_deal_id=False):
    """The archived order with this number belonging to the user's active cabinet.

    `by_deal_id` looks the order up by its счёт-фактура number (`deal_id`)
    instead of its ТТН — the accounting feedback flow keys on that.
    """
    number = (number or "").strip()
    if not number:
        return None

    cabinet = await Cabinet.objects.filter(
        bot_user__user_id=user_id, is_active=True
    ).select_related("client").afirst()
    if not (cabinet and cabinet.client):
        return None

    field = "deal_id" if by_deal_id else "delivery_number"
    return await Order.objects.filter(
        client=cabinet.client, status="A", **{field: number}
    ).afirst()


def strip_marker(text):
    """Remove the @@@ marker from an admin reply, keeping the rest intact."""
    if not text:
        return ""
    return text.replace(ANSWER_MARKER, "").strip()


def has_marker(text):
    return bool(text) and ANSWER_MARKER in text


async def get_feedback_by_admin_message(message_id):
    """Find the feedback whose admin-group message was replied to."""
    return await Feedback.objects.filter(
        admin_message_id=message_id
    ).select_related("bot_user", "client").afirst()


async def save_answer(feedback, answer, admin_user_id=None, admin_name=None,
                      file_id=None, file_type=None):
    """Store an admin's reply (text and/or attachment) on an existing Feedback."""
    feedback.answer = answer or ""
    feedback.answer_file_id = file_id
    feedback.answer_file_type = file_type
    feedback.answered_by = admin_user_id
    feedback.answered_by_name = admin_name
    feedback.answered_at = timezone.now()
    await feedback.asave(update_fields=[
        "answer", "answer_file_id", "answer_file_type",
        "answered_by", "answered_by_name", "answered_at",
    ])
    return feedback


def _number_line(feedback: Feedback):
    """The "<label>: <number>" line, or nothing when there is no number."""
    if not feedback.ttn_number:
        return ""
    return NUMBER_LINE.format(
        label=feedback.number_label,
        number=html.escape(feedback.ttn_number),
    )


def admin_feedback_text(feedback: Feedback):
    return ADMIN_FEEDBACK_TEXT.format(
        feedback_type=feedback.get_feedback_type_display(),
        number_line=_number_line(feedback),
        client=html.escape(feedback.client.name if feedback.client else "—"),
        phone=html.escape(feedback.bot_user.phone or "—") if feedback.bot_user else "—",
        text=html.escape(feedback.text),
        attachment=ATTACHMENT_NOTE if feedback.file_id else "",
    )


def admin_answered_text(feedback: Feedback, admin_name=None):
    answer = feedback.answer or ""
    if feedback.answer_file_id and not answer:
        answer = "\U0001F4CE вложение"
    return ADMIN_ANSWERED_TEXT.format(
        feedback_type=feedback.get_feedback_type_display(),
        number_line=_number_line(feedback),
        client=html.escape(feedback.client.name if feedback.client else "—"),
        text=html.escape(feedback.text),
        attachment=ATTACHMENT_NOTE if feedback.file_id else "",
        admin=html.escape(admin_name or feedback.answered_by_name or "—"),
        answer=html.escape(answer),
    )
