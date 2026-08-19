import html

from django.utils import timezone

from bot.models import Bot_user, Cabinet, Feedback


ADMIN_FEEDBACK_TEXT = """\U0001F4DD <b>Новое обращение от клиента</b>
<b>Номер ТТН:</b> <code>{ttn_number}</code>
<b>Клиент:</b> {client}
<b>Телефон:</b> {phone}

<b>Обращение:</b>
{text}"""

ANSWER_MARKER = "@@@"

ADMIN_ANSWERED_TEXT = """✅ <b>Обращение обработано</b>
<b>Номер ТТН:</b> <code>{ttn_number}</code>
<b>Клиент:</b> {client}

<b>Обращение:</b>
{text}

<b>Ответ ({admin}):</b>
{answer}"""


def create_feedback(user_id, ttn_number, text):
    """Store a client's feedback. Returns the Feedback, or None if the user is unknown."""
    bot_user = Bot_user.objects.filter(user_id=user_id).first()
    if not bot_user:
        return None

    cabinet = Cabinet.objects.filter(
        bot_user=bot_user, is_active=True
    ).select_related("client").first()

    return Feedback.objects.create(
        bot_user=bot_user,
        client=cabinet.client if cabinet else None,
        ttn_number=ttn_number,
        text=text,
    )


def strip_marker(text):
    """Remove the @@@ marker from an admin reply, keeping the rest intact."""
    if not text:
        return ""
    return text.replace(ANSWER_MARKER, "").strip()


def has_marker(text):
    return bool(text) and ANSWER_MARKER in text


def get_feedback_by_admin_message(message_id):
    """Find the feedback whose admin-group message was replied to."""
    return Feedback.objects.filter(
        admin_message_id=message_id
    ).select_related("bot_user", "client").first()


def save_answer(feedback, answer, admin_user_id=None, admin_name=None,
                file_id=None, file_type=None):
    """Store an admin's reply (text and/or attachment) on an existing Feedback."""
    feedback.answer = answer or ""
    feedback.answer_file_id = file_id
    feedback.answer_file_type = file_type
    feedback.answered_by = admin_user_id
    feedback.answered_by_name = admin_name
    feedback.answered_at = timezone.now()
    feedback.save(update_fields=[
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
    )


def admin_answered_text(feedback: Feedback, admin_name=None):
    answer = feedback.answer or ""
    if feedback.answer_file_id and not answer:
        answer = "\U0001F4CE вложение"
    return ADMIN_ANSWERED_TEXT.format(
        ttn_number=html.escape(feedback.ttn_number),
        client=html.escape(feedback.client.name if feedback.client else "—"),
        text=html.escape(feedback.text),
        admin=html.escape(admin_name or feedback.answered_by_name or "—"),
        answer=html.escape(answer),
    )
