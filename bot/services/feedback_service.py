import html

from django.utils import timezone

from app.models import Order
from bot.models import Bot_user, Cabinet, Feedback


ADMIN_FEEDBACK_TEXT = """\U0001F4DD <b>Новое обращение от клиента</b>
<b>Номер ТТН:</b> <code>{ttn_number}</code>
<b>Клиент:</b> {client}
<b>Телефон:</b> {phone}

<b>Обращение:</b>
{text}{attachment}"""

ATTACHMENT_NOTE = "\n\n\U0001F4CE К обращению приложен файл."

ANSWER_MARKER = "@@@"

# Telegram allows at most 50 inline results per answer
INLINE_RESULT_LIMIT = 50

ADMIN_ANSWERED_TEXT = """✅ <b>Обращение обработано</b>
<b>Номер ТТН:</b> <code>{ttn_number}</code>
<b>Клиент:</b> {client}

<b>Обращение:</b>
{text}{attachment}

<b>Ответ ({admin}):</b>
{answer}"""


async def create_feedback(user_id, ttn_number, text, file_id=None, file_type=None):
    """Store a client's feedback. Returns the Feedback, or None if the user is unknown."""
    bot_user = await Bot_user.objects.filter(user_id=user_id).afirst()
    if not bot_user:
        return None

    cabinet = await Cabinet.objects.filter(
        bot_user=bot_user, is_active=True
    ).select_related("client").afirst()

    return await Feedback.objects.acreate(
        bot_user=bot_user,
        client=cabinet.client if cabinet else None,
        ttn_number=ttn_number,
        text=text,
        file_id=file_id,
        file_type=file_type,
    )


async def search_client_orders(user_id, query="", limit=INLINE_RESULT_LIMIT):
    """Archived ("A") orders of the user's active cabinet, matched by deal_id prefix.

    Feeds the TTN inline-query search; returns [] when the user has no cabinet.
    Prefix (not substring) matching, so a query must start the TTN — this is
    what lets the lookup use an index instead of scanning.
    """
    cabinet = await Cabinet.objects.filter(
        bot_user__user_id=user_id, is_active=True
    ).select_related("client").afirst()
    if not (cabinet and cabinet.client):
        return []

    orders = Order.objects.filter(client=cabinet.client, status="A")
    query = (query or "").strip()
    if query:
        orders = orders.filter(deal_id__istartswith=query)

    return [o async for o in orders.order_by("-deal_datetime", "-id")[:limit]]


async def find_client_order(user_id, deal_id):
    """The archived order with this deal_id belonging to the user's active cabinet."""
    deal_id = (deal_id or "").strip()
    if not deal_id:
        return None

    cabinet = await Cabinet.objects.filter(
        bot_user__user_id=user_id, is_active=True
    ).select_related("client").afirst()
    if not (cabinet and cabinet.client):
        return None

    return await Order.objects.filter(
        client=cabinet.client, status="A", deal_id=deal_id
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


def admin_feedback_text(feedback: Feedback):
    return ADMIN_FEEDBACK_TEXT.format(
        ttn_number=html.escape(feedback.ttn_number),
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
        ttn_number=html.escape(feedback.ttn_number),
        client=html.escape(feedback.client.name if feedback.client else "—"),
        text=html.escape(feedback.text),
        attachment=ATTACHMENT_NOTE if feedback.file_id else "",
        admin=html.escape(admin_name or feedback.answered_by_name or "—"),
        answer=html.escape(answer),
    )
