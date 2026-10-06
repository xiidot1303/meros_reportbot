from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

from bot.models import Feedback
from bot.resources.strings import Strings
from bot.services.feedback_service import (
    TAKE_BUTTON_TEXT,
    TAKE_CALLBACK_PREFIX,
    admin_answered_text,
    admin_feedback_text,
    admin_in_progress_text,
    get_admin_chat_id,
)


def _client_number_line(feedback: Feedback, words: Strings):
    """The "<label>: <number>" line for the client, or nothing for anonymous."""
    if not feedback.ttn_number:
        return ""
    label = (words.feedback_number_label_factura
             if feedback.feedback_type == Feedback.ACCOUNTING
             else words.feedback_number_label_ttn)
    return words.feedback_number_line.format(
        label=label, number=feedback.ttn_number)


SENDABLE = ("photo", "video", "document", "audio", "voice",
            "animation", "video_note", "sticker")
CAPTIONLESS = ("video_note", "sticker")


async def _send_with_attachment(bot, chat_id, text, file_id, file_type, reply_markup=None):
    """Send text plus an optional attachment, and return the message carrying the text.

    The text message is the one admins reply to, so for captionless media
    (video_note, sticker) the text is sent first and returned.
    """
    send = getattr(bot, f"send_{file_type}", None) if file_type in SENDABLE else None

    if not (file_id and send):
        return await bot.send_message(
            chat_id=chat_id, text=text, parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )

    if file_type in CAPTIONLESS:
        message = await bot.send_message(
            chat_id=chat_id, text=text, parse_mode=ParseMode.HTML,
            reply_markup=reply_markup,
        )
        await send(chat_id, file_id)
        return message

    return await send(
        chat_id, file_id, caption=text, parse_mode=ParseMode.HTML,
        reply_markup=reply_markup,
    )


async def notify_new_feedback(feedback: Feedback):
    """Confirm to the client, then post the feedback into the admin group —
    the region's group for a warehouse feedback, see `get_admin_chat_id`.
    Admins answer by replying to that message with @@@ in the text/caption."""
    from bot.control.updater import application

    # bot_user is already loaded — acreate() assigned the instance and
    # get_feedback_by_admin_message() select_related()s it — so this is a plain
    # attribute read, not a lazy FK query.
    bot_user = feedback.bot_user
    if bot_user and bot_user.user_id:
        words = Strings(user_id=bot_user.user_id)
        await application.bot.send_message(
            chat_id=bot_user.user_id,
            text=words.feedback_sent.format(
                number_line=_client_number_line(feedback, words)
            ),
            parse_mode=ParseMode.HTML,
        )

    chat_id = await get_admin_chat_id(feedback)
    if not chat_id:
        return

    text = admin_feedback_text(feedback)
    message = await _send_with_attachment(
        bot=application.bot,
        chat_id=chat_id,
        text=text,
        file_id=feedback.file_id,
        file_type=feedback.file_type,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(
            text=TAKE_BUTTON_TEXT,
            callback_data=f"{TAKE_CALLBACK_PREFIX}{feedback.pk}",
        )]]),
    )

    feedback.admin_chat_id = chat_id
    feedback.admin_message_id = message.message_id
    await feedback.asave(
        update_fields=["admin_chat_id", "admin_message_id", "updated_at"])


async def notify_client_in_review(feedback: Feedback, bot):
    """Tell the client a staff member has taken their feedback."""
    bot_user = feedback.bot_user
    if not (bot_user and bot_user.user_id):
        return False

    words = Strings(user_id=bot_user.user_id)
    await bot.send_message(
        chat_id=bot_user.user_id,
        text=words.feedback_in_review.format(
            number_line=_client_number_line(feedback, words)
        ),
        parse_mode=ParseMode.HTML,
    )
    return True


async def send_answer_to_client(feedback: Feedback, bot):
    """Deliver the admin's answer — text and/or attachment — to the client."""
    bot_user = feedback.bot_user
    if not (bot_user and bot_user.user_id):
        return False

    words = Strings(user_id=bot_user.user_id)
    caption = words.feedback_answer.format(
        number_line=_client_number_line(feedback, words),
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


async def _edit_admin_message(feedback: Feedback, bot, text):
    """Rewrite the feedback's group message, which also drops the take button."""
    if not (feedback.admin_chat_id and feedback.admin_message_id):
        return

    try:
        await bot.edit_message_text(
            chat_id=feedback.admin_chat_id,
            message_id=feedback.admin_message_id,
            text=text,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        # the feedback came with a file, so the group message is a caption
        try:
            await bot.edit_message_caption(
                chat_id=feedback.admin_chat_id,
                message_id=feedback.admin_message_id,
                caption=text,
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass


async def mark_admin_message_in_progress(feedback: Feedback, bot):
    """Show in the group who took the feedback, so nobody else picks it up."""
    await _edit_admin_message(feedback, bot, admin_in_progress_text(feedback))


async def mark_admin_message_answered(feedback: Feedback, bot):
    """Edit the admin-group message so handled feedback is visible at a glance."""
    await _edit_admin_message(feedback, bot, admin_answered_text(feedback))
