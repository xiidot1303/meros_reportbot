from telegram.constants import ParseMode

from config import ADMIN_GROUP_ID
from bot.models import Feedback
from bot.resources.strings import Strings
from bot.services.feedback_service import admin_answered_text, admin_feedback_text


SENDABLE = ("photo", "video", "document", "audio", "voice",
            "animation", "video_note", "sticker")
CAPTIONLESS = ("video_note", "sticker")


async def _send_with_attachment(bot, chat_id, text, file_id, file_type):
    """Send text plus an optional attachment, and return the message carrying the text.

    The text message is the one admins reply to, so for captionless media
    (video_note, sticker) the text is sent first and returned.
    """
    send = getattr(bot, f"send_{file_type}", None) if file_type in SENDABLE else None

    if not (file_id and send):
        return await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)

    if file_type in CAPTIONLESS:
        message = await bot.send_message(
            chat_id=chat_id, text=text, parse_mode=ParseMode.HTML
        )
        await send(chat_id, file_id)
        return message

    return await send(chat_id, file_id, caption=text, parse_mode=ParseMode.HTML)


async def notify_new_feedback(feedback: Feedback):
    """Confirm to the client, then post the feedback into the admin group.
    Admins answer by replying to that message with @@@ in the text/caption."""
    from bot.control.updater import application

    # bot_user is already loaded — acreate() assigned the instance and
    # get_feedback_by_admin_message() select_related()s it — so this is a plain
    # attribute read, not a lazy FK query.
    bot_user = feedback.bot_user
    if bot_user and bot_user.user_id:
        await application.bot.send_message(
            chat_id=bot_user.user_id,
            text=Strings(user_id=bot_user.user_id).feedback_sent.format(
                ttn_number=feedback.ttn_number
            ),
            parse_mode=ParseMode.HTML,
        )

    if not ADMIN_GROUP_ID:
        return

    text = admin_feedback_text(feedback)
    message = await _send_with_attachment(
        bot=application.bot,
        chat_id=ADMIN_GROUP_ID,
        text=text,
        file_id=feedback.file_id,
        file_type=feedback.file_type,
    )

    feedback.admin_message_id = message.message_id
    await feedback.asave(update_fields=["admin_message_id"])


async def send_answer_to_client(feedback: Feedback, bot):
    """Deliver the admin's answer — text and/or attachment — to the client."""
    bot_user = feedback.bot_user
    if not (bot_user and bot_user.user_id):
        return False

    caption = Strings(user_id=bot_user.user_id).feedback_answer.format(
        ttn_number=feedback.ttn_number,
        answer=feedback.answer or "",
    )

    await _send_with_attachment(
        bot=bot,
        chat_id=bot_user.user_id,
        text=caption,
        file_id=feedback.answer_file_id,
        file_type=feedback.answer_file_type,
    )

    return True


async def mark_admin_message_answered(feedback: Feedback, bot):
    """Edit the admin-group message so handled feedback is visible at a glance."""
    if not (ADMIN_GROUP_ID and feedback.admin_message_id):
        return

    text = admin_answered_text(feedback)
    try:
        await bot.edit_message_text(
            chat_id=ADMIN_GROUP_ID,
            message_id=feedback.admin_message_id,
            text=text,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        # the feedback came with a file, so the group message is a caption
        try:
            await bot.edit_message_caption(
                chat_id=ADMIN_GROUP_ID,
                message_id=feedback.admin_message_id,
                caption=text,
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
