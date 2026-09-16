"""Admin-only `/update_phones`: bulk-update SmartUp phone numbers from xlsx.

Only ids listed in `ADMIN_USER_IDS` reach this conversation, and the command is
only advertised in their Telegram command menu (see
[bot/control/commands.py](bot/control/commands.py)) — the guard here is what
actually enforces it, since a non-admin can always type the command by hand.

The work itself is slow: the SmartUp export is a single large response and the
import runs in batches, so a run takes minutes. It is handed to
`application.create_task` and the admin is told immediately, rather than being
left with a hung conversation. The whole blocking part lives in
[app/services/legal_person_service.py](app/services/legal_person_service.py)
and is pushed onto a worker thread so the bot's event loop keeps serving
clients while it runs.
"""

import asyncio
import html
import io
import logging
import time

from bot.bot import *
from bot.services.admin_service import is_admin


logger = logging.getLogger(__name__)


# Telegram's own bot-API download cap is 20 MB; a phone list is a few hundred
# KB, so anything near the cap is a mistaken upload rather than a real one.
MAX_FILE_BYTES = 10 * 1024 * 1024

# At most this many missing ТИНs are listed back; the full count is always
# reported, but a 4096-character message cannot hold hundreds of them.
MAX_LISTED_NOT_FOUND = 30

# `user_data` is persisted by DjangoPersistence, so this flag outlives a
# restart. A run killed mid-flight (deploy, watchdog reload, `Application.stop`
# cancelling its tasks) would therefore wedge the command permanently. The
# start time is stored alongside it so the lock can expire instead — see
# `_lock_state`.
RUNNING_FLAG = "update_phones_running"
RUNNING_SINCE = "update_phones_started_at"

# A real run is export (up to 5 min) plus batched imports. Past this, the flag
# is assumed to be a leftover rather than a live run.
STALE_LOCK_SECONDS = 30 * 60


def _lock_state(context: CustomContext):
    """Is a run in progress, and is that claim still believable?

    Returns `(running, stale)`. `stale` means the flag is set but too old to
    be a live run — the previous one died without clearing it.
    """
    if not context.user_data.get(RUNNING_FLAG):
        return False, False

    started_at = context.user_data.get(RUNNING_SINCE)
    if not started_at:
        # set by an older build that stored no timestamp; never trust it
        return True, True
    return True, (time.time() - started_at) > STALE_LOCK_SECONDS


def _acquire_lock(context: CustomContext):
    context.user_data[RUNNING_FLAG] = True
    context.user_data[RUNNING_SINCE] = time.time()


def _release_lock(context: CustomContext):
    context.user_data[RUNNING_FLAG] = False
    context.user_data.pop(RUNNING_SINCE, None)


async def ask_file(update: Update, context: CustomContext):
    """Entry point for /update_phones."""
    if not is_admin(update.effective_user.id):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=context.words.admin_only,
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END

    running, stale = _lock_state(context)
    if running and not stale:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=context.words.update_phones_already_running,
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END

    if stale:
        # the previous run never reported back; say so and let this one through
        _release_lock(context)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=context.words.update_phones_stale_lock,
            parse_mode=ParseMode.HTML,
        )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.update_phones_ask_file,
        parse_mode=ParseMode.HTML,
    )
    return GET_PHONES_FILE


async def cancel(update: Update, context: CustomContext):
    # doubles as the manual way out of a wedged lock
    _release_lock(context)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.update_phones_cancelled,
        parse_mode=ParseMode.HTML,
    )
    return ConversationHandler.END


async def get_file(update: Update, context: CustomContext):
    """Accept the workbook, then run the update in the background.

    Only `.xlsx` is accepted — the format was agreed with the client, and a
    `.xls` or a CSV would parse into something that silently writes the wrong
    phones into SmartUp.
    """
    if not is_admin(update.effective_user.id):
        return ConversationHandler.END

    document = update.message.document
    filename = (document.file_name or "").lower()

    if not filename.endswith(".xlsx"):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=context.words.update_phones_wrong_file,
            parse_mode=ParseMode.HTML,
        )
        return GET_PHONES_FILE

    if document.file_size and document.file_size > MAX_FILE_BYTES:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=context.words.update_phones_too_large.format(
                limit=MAX_FILE_BYTES // (1024 * 1024)),
            parse_mode=ParseMode.HTML,
        )
        return GET_PHONES_FILE

    telegram_file = await document.get_file()
    file_bytes = bytes(await telegram_file.download_as_bytearray())

    _acquire_lock(context)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.update_phones_started,
        parse_mode=ParseMode.HTML,
    )

    # Detached on purpose: the conversation ends here and the admin gets the
    # result as a separate message whenever the run finishes.
    context.application.create_task(
        _run_update(context, update.effective_chat.id, file_bytes),
        update=update,
    )

    return ConversationHandler.END


async def _run_update(context: CustomContext, chat_id, file_bytes):
    """Do the update and report back. Never lets an exception escape silently."""
    from app.services.legal_person_service import (
        WorkbookFormatError, update_phone_numbers,
    )

    try:
        progress_queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def progress(stage):
            # called from the worker thread
            loop.call_soon_threadsafe(progress_queue.put_nowait, stage)

        worker = asyncio.create_task(
            asyncio.to_thread(update_phone_numbers, io.BytesIO(file_bytes), progress)
        )
        reporter = asyncio.create_task(
            _report_progress(context, chat_id, progress_queue))

        try:
            result = await worker
        finally:
            reporter.cancel()

        await _send_result(context, chat_id, result)

    except WorkbookFormatError:
        await context.bot.send_message(
            chat_id=chat_id,
            text=context.words.update_phones_bad_format,
            parse_mode=ParseMode.HTML,
        )
    except asyncio.CancelledError:
        # CancelledError is a BaseException, so it used to slip past the
        # `except Exception` below and the admin was told nothing at all.
        # `Application.stop()` cancels outstanding create_task tasks, so this
        # is what a deploy or a watchdog reload mid-run looks like.
        logger.warning("/update_phones cancelled mid-run")
        await _notify_interrupted(context, chat_id)
        raise
    except Exception as exc:
        logger.exception("/update_phones failed")
        await context.bot.send_message(
            chat_id=chat_id,
            text=context.words.update_phones_failed.format(
                error=html.escape(str(exc))[:500] or type(exc).__name__),
            parse_mode=ParseMode.HTML,
        )
    except BaseException:
        # anything else that is not an Exception (e.g. a hard kill path) still
        # must not leave the admin staring at a silent chat
        logger.exception("/update_phones died")
        await _notify_interrupted(context, chat_id)
        raise
    finally:
        _release_lock(context)


async def _notify_interrupted(context: CustomContext, chat_id):
    """Tell the admin the run stopped early. Never raises.

    Called while an exception is propagating — often a cancellation — so a
    failure to send here must not replace the original one.
    """
    try:
        await asyncio.shield(context.bot.send_message(
            chat_id=chat_id,
            text=context.words.update_phones_interrupted,
            parse_mode=ParseMode.HTML,
        ))
    except Exception:
        logger.warning("could not report interruption", exc_info=True)


async def _report_progress(context: CustomContext, chat_id, queue):
    """Relay the worker's stage changes to the admin until cancelled."""
    messages = {
        "export": "update_phones_progress_export",
        "import": "update_phones_progress_import",
    }
    try:
        while True:
            stage = await queue.get()
            key = messages.get(stage)
            if not key:
                continue
            try:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=getattr(context.words, key),
                    parse_mode=ParseMode.HTML,
                )
            except Exception:
                # a lost progress ping must not affect the run itself
                logger.warning("progress message failed", exc_info=True)
    except asyncio.CancelledError:
        return


async def _send_result(context: CustomContext, chat_id, result):
    """The summary the admin actually reads."""
    not_found = result["not_found"]

    if result["failed_batches"] and not result["updated"]:
        # nothing was written — a success headline with "updated: 0" underneath
        # reads as "done" and hides a total failure
        await context.bot.send_message(
            chat_id=chat_id,
            text=context.words.update_phones_all_failed.format(
                count=result["failed_batches"],
                total=result["total"],
                not_found=len(not_found),
            ),
            parse_mode=ParseMode.HTML,
            reply_markup=await main_menu_keyboard(context),
        )
        return

    text = context.words.update_phones_done.format(
        total=result["total"],
        updated=result["updated"],
        unchanged=result["unchanged"],
        not_found=len(not_found),
        skipped=result["skipped"],
    )

    if not_found:
        listed = not_found[:MAX_LISTED_NOT_FOUND]
        rendered = ", ".join(html.escape(tin) for tin in listed)
        if len(not_found) > len(listed):
            rendered += f", … (+{len(not_found) - len(listed)})"
        text += context.words.update_phones_not_found_list.format(tins=rendered)

    if result["failed_batches"]:
        text += context.words.update_phones_partial_failure.format(
            count=result["failed_batches"])

    await context.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=await main_menu_keyboard(context),
    )
