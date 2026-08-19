from bot.bot import *
from bot.services.feedback_notifier import (
    mark_admin_message_answered,
    send_answer_to_client,
)
from bot.services.feedback_service import (
    get_feedback_by_admin_message,
    has_marker,
    save_answer,
    strip_marker,
)
from config import ADMIN_GROUP_ID


ADMIN_REPLY_SENT = "✅ Ответ отправлен клиенту."
ADMIN_REPLY_NO_USER = "⚠️ Не удалось отправить ответ: клиент недоступен."


def _extract_attachment(message):
    """Return (file_id, file_type) for whatever media the admin attached."""
    if message.photo:
        return message.photo[-1].file_id, "photo"
    for attr in ("video", "document", "audio", "voice", "animation", "video_note", "sticker"):
        media = getattr(message, attr, None)
        if media:
            return media.file_id, attr
    return None, None


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
