from asgiref.sync import sync_to_async
from telegram.constants import ParseMode

from config import ADMIN_GROUP_ID
from bot.models import Feedback
from bot.resources.strings import Strings
from bot.services.feedback_service import admin_answered_text, admin_feedback_text


SENDABLE = ("photo", "video", "document", "audio", "voice",
            "animation", "video_note", "sticker")
CAPTIONLESS = ("video_note", "sticker")


async def notify_new_feedback(feedback: Feedback):
    """Confirm to the client, then post the feedback into the admin group.
    Admins answer by replying to that message with @@@ in the text/caption."""
    from bot.control.updater import application

    bot_user = await sync_to_async(lambda: feedback.bot_user)()
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

    text = await sync_to_async(admin_feedback_text)(feedback)
    message = await application.bot.send_message(
        chat_id=ADMIN_GROUP_ID,
        text=text,
        parse_mode=ParseMode.HTML,
    )

    feedback.admin_message_id = message.message_id
    await feedback.asave(update_fields=["admin_message_id"])


async def send_answer_to_client(feedback: Feedback, bot):
    """Deliver the admin's answer — text and/or attachment — to the client."""
    bot_user = await sync_to_async(lambda: feedback.bot_user)()
    if not (bot_user and bot_user.user_id):
        return False

    caption = Strings(user_id=bot_user.user_id).feedback_answer.format(
        ttn_number=feedback.ttn_number,
        answer=feedback.answer or "",
    )

    file_id, file_type = feedback.answer_file_id, feedback.answer_file_type
    send = getattr(bot, f"send_{file_type}", None) if file_type in SENDABLE else None

    if file_id and send:
        # video_note and sticker take no caption — send the text separately
        if file_type in CAPTIONLESS:
            await bot.send_message(
                chat_id=bot_user.user_id, text=caption, parse_mode=ParseMode.HTML
            )
            await send(bot_user.user_id, file_id)
        else:
            await send(bot_user.user_id, file_id, caption=caption, parse_mode=ParseMode.HTML)
    else:
        await bot.send_message(
            chat_id=bot_user.user_id, text=caption, parse_mode=ParseMode.HTML
        )

    return True


async def mark_admin_message_answered(feedback: Feedback, bot):
    """Edit the admin-group message so handled feedback is visible at a glance."""
    if not (ADMIN_GROUP_ID and feedback.admin_message_id):
        return
    try:
        await bot.edit_message_text(
            chat_id=ADMIN_GROUP_ID,
            message_id=feedback.admin_message_id,
            text=await sync_to_async(admin_answered_text)(feedback),
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass
