"""Hand the client a price-list xlsx.

The files themselves are built by the sync job
([app/scheduled_job/price_job.py](app/scheduled_job/price_job.py)), so nothing
here generates a workbook — this module only picks the right published file and
sends it. The first send caches Telegram's `file_id`, and later clicks resend by
that id instead of re-uploading ~1 MB.
"""

import asyncio

from asgiref.sync import sync_to_async

from bot.bot import *
from app.models import PriceListFile, ProductPrice


# callback_data prefix for the type picker
PRICE_TYPE_PREFIX = "price_type_"


async def _ask_price_type(update: Update, context: CustomContext):
    """Entry point: which of the two price lists does the client want?"""
    if update.callback_query:
        await update.callback_query.edit_message_reply_markup(None)

    buttons = [
        [InlineKeyboardButton(
            text=context.words.price_list_type_negotiated,
            callback_data=f"{PRICE_TYPE_PREFIX}{ProductPrice.PREPAYMENT_25}",
        )],
        [InlineKeyboardButton(
            text=context.words.price_list_type_prepayment_100,
            callback_data=f"{PRICE_TYPE_PREFIX}{ProductPrice.PREPAYMENT_100}",
        )],
        [InlineKeyboardButton(
            text=context.words.main_menu,
            callback_data="main_menu",
        )],
    ]

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.price_list_type_prompt,
        parse_mode=ParseMode.HTML,
        reply_markup=InlineKeyboardMarkup(buttons),
    )

    return SELECT_PRICE_TYPE


@sync_to_async
def _get_price_list_file(price_type_id):
    """The published file for this type, or None if it is missing on disk."""
    record = PriceListFile.objects.filter(price_type_id=price_type_id).first()
    if not record or not record.exists:
        return None
    return record


@sync_to_async
def _cache_file_id(price_type_id, file_id):
    """Remember Telegram's id so the next click skips the upload."""
    PriceListFile.objects.filter(price_type_id=price_type_id).update(
        telegram_file_id=file_id)


async def send_price_list(update: Update, context: CustomContext):
    """Send the file for the picked type, uploading only when not yet cached."""
    query = update.callback_query
    await query.edit_message_reply_markup(None)

    price_type_id = int(query.data.removeprefix(PRICE_TYPE_PREFIX))
    record = await _get_price_list_file(price_type_id)

    if record is None:
        # No sync has completed yet, or the file vanished from disk.
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=context.words.price_list_not_ready,
            parse_mode=ParseMode.HTML,
            reply_markup=await main_menu_keyboard(context),
        )
        return ConversationHandler.END

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.price_list_loading,
        parse_mode=ParseMode.HTML,
    )
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_DOCUMENT)

    caption = context.words.price_list_document.format(
        price_type=record.get_price_type_id_display(),
        count=record.row_count,
        # the file is up to one sync interval old; say so rather than implying
        # it is live
        generated_at=record.generated_at.strftime("%d.%m.%Y %H:%M"),
    )

    try:
        message = await _send_document(context, update, record, caption)
    except Exception:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=context.words.price_list_error,
            parse_mode=ParseMode.HTML,
            reply_markup=await main_menu_keyboard(context),
        )
        return ConversationHandler.END

    if message and message.document and not record.telegram_file_id:
        await _cache_file_id(price_type_id, message.document.file_id)

    return ConversationHandler.END


async def _send_document(context: CustomContext, update: Update, record, caption):
    """Resend by cached file_id when we have one, otherwise upload the file.

    A cached id can go stale (Telegram drops it, or the file was replaced
    between the lookup and the send), so a failed resend falls back to a real
    upload instead of surfacing an error to the client.
    """
    from app.services.price_report_service import client_facing_filename

    chat_id = update.effective_chat.id
    filename = client_facing_filename(record.price_type_id, record.generated_at)

    if record.telegram_file_id:
        try:
            return await context.bot.send_document(
                chat_id=chat_id,
                document=record.telegram_file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=await main_menu_keyboard(context),
            )
        except Exception:
            await _cache_file_id(record.price_type_id, None)

    document = await asyncio.to_thread(_read_file, record.path, filename)
    return await context.bot.send_document(
        chat_id=chat_id,
        document=document,
        filename=filename,
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=await main_menu_keyboard(context),
    )


def _read_file(path, filename):
    """Read the workbook off disk; runs in a worker thread."""
    import io

    with open(path, "rb") as handle:
        document = io.BytesIO(handle.read())
    document.name = filename
    return document
