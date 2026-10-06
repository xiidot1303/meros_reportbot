import html

from asgiref.sync import sync_to_async
from django.utils import timezone

from app.models import Order, Warehouse
from bot.models import Bot_user, Cabinet, Feedback
from config import ADMIN_GROUP_ID


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

# the button under a new feedback in the admin group; its callback carries the pk
TAKE_BUTTON_TEXT = "\U0001F64B Взять в работу"
TAKE_CALLBACK_PREFIX = "feedback_take_"

IN_PROGRESS_NOTE = "\n\n\U0001F504 <b>На рассмотрении:</b> {admin} ({taken_at})"

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


async def get_feedback_by_admin_message(chat_id, message_id):
    """Find the feedback whose admin-group message was replied to."""
    return await Feedback.objects.filter(
        admin_chat_id=chat_id, admin_message_id=message_id
    ).select_related("bot_user", "client").afirst()


async def get_admin_chat_id(feedback: Feedback):
    """The group a new feedback is posted to.

    Warehouse feedback goes to the group of the oblast whose warehouse shipped
    the order (by its ТТН); everything else — and any warehouse feedback whose
    order, warehouse or region group can't be resolved — goes to ADMIN_GROUP_ID.
    """
    if (feedback.feedback_type == Feedback.WAREHOUSE
            and feedback.ttn_number and feedback.client_id):
        order = await Order.objects.filter(
            client_id=feedback.client_id,
            delivery_number=feedback.ttn_number,
        ).exclude(warehouse_id__isnull=True).order_by("-id").afirst()
        if order:
            group_id = await sync_to_async(Warehouse.feedback_group_id)(
                order.warehouse_id)
            if group_id:
                return group_id
    return ADMIN_GROUP_ID or None


async def save_answer(feedback, answer, admin_user_id=None, admin_name=None,
                      file_id=None, file_type=None):
    """Store an admin's reply (text and/or attachment) on an existing Feedback."""
    feedback.answer = answer or ""
    feedback.answer_file_id = file_id
    feedback.answer_file_type = file_type
    feedback.answered_by = admin_user_id
    feedback.answered_by_name = admin_name
    feedback.answered_at = timezone.now()
    feedback.status = Feedback.ANSWERED
    await feedback.asave(update_fields=[
        "answer", "answer_file_id", "answer_file_type",
        "answered_by", "answered_by_name", "answered_at",
        "status", "updated_at",
    ])
    return feedback


async def take_feedback(feedback_id, chat_id, admin_user_id, admin_name):
    """A staff member pressed "take" on the group message.

    Returns `(feedback, taken)`: `taken` is False when someone else got there
    first or it is already answered — the update is conditional on the status
    still being NEW, so two admins clicking at once can't both take it.
    `feedback` is None when no feedback was posted under this id in this chat.
    """
    now = timezone.now()
    taken = await Feedback.objects.filter(
        pk=feedback_id, admin_chat_id=chat_id, status=Feedback.NEW,
    ).aupdate(
        status=Feedback.IN_PROGRESS,
        taken_by=admin_user_id,
        taken_by_name=admin_name,
        taken_at=now,
        updated_at=now,
    )
    feedback = await Feedback.objects.filter(
        pk=feedback_id, admin_chat_id=chat_id,
    ).select_related("bot_user", "client").afirst()
    return feedback, bool(taken)


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


def admin_in_progress_text(feedback: Feedback):
    """The group message once a staff member has taken the feedback."""
    return admin_feedback_text(feedback) + IN_PROGRESS_NOTE.format(
        admin=html.escape(feedback.taken_by_name or "—"),
        taken_at=feedback.taken_at.strftime("%d.%m.%Y %H:%M") if feedback.taken_at else "—",
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
