"""Report unhandled exceptions from the `app` side to the developer's Telegram.

The `bot` side already has PTB's error handler ([bot/bot/main.py](bot/bot/main.py)),
so this covers the half that has no such net: scheduled jobs, Celery tasks,
external-API calls and the inbound API views.

Delivery reuses the normal notification path — a Celery task posting to
`{NEWSLETTER_URL}/send-newsletter/` — so nothing here talks to Telegram directly
and the app/bot split stays intact.
"""

import functools
import hashlib
import html
import logging
import traceback

from django.core.cache import cache

from core.celery import app
from config import DEVELOPER_USER_ID


logger = logging.getLogger(__name__)


# Telegram rejects any message over 4096 characters, so every variable-length
# part is capped and the rendered result is capped again as a backstop.
MAX_MESSAGE_CHARS = 4096
MAX_TRACEBACK_CHARS = 2500
MAX_EXC_MESSAGE_CHARS = 500
MAX_CONTEXT_VALUE_CHARS = 200

# Don't re-send the same failure from the same place more often than this.
# A job that runs every 7 minutes and fails every time would otherwise flood
# the developer's chat.
DUPLICATE_SILENCE_SECONDS = 1800

ERROR_MESSAGE = """\U0001F6A8 <b>Ошибка в приложении</b>
<b>Где:</b> <code>{location}</code>
<b>Тип:</b> <code>{exc_type}</code>

<b>Сообщение:</b>
<code>{exc_message}</code>
{context}
<b>Traceback:</b>
<pre>{traceback}</pre>"""


def _truncate_tail(text, limit):
    """Keep the tail — the innermost frames are where the error actually is."""
    if len(text) <= limit:
        return text
    return "...\n" + text[-limit:]


def _truncate_head(text, limit):
    """Keep the start — for messages, the first line carries the meaning."""
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _fingerprint(location, exc):
    """Identify "the same error from the same place" for de-duplication."""
    raw = f"{location}:{type(exc).__name__}:{exc}"
    return "app:error:" + hashlib.md5(raw.encode("utf-8", "replace")).hexdigest()


def _should_send(location, exc):
    """True the first time this error is seen, False while it is still silenced."""
    try:
        # add() only succeeds if the key is absent, so this is atomic
        return cache.add(_fingerprint(location, exc), 1, DUPLICATE_SILENCE_SECONDS)
    except Exception:
        # a broken cache must not suppress the alert
        return True


def build_error_message(location, exc, context=None):
    """Render the developer-facing report for one exception."""
    try:
        tb = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        ) or repr(exc)
    except Exception:
        tb = repr(exc)

    context_block = ""
    if context:
        rendered = "\n".join(
            "<b>{}:</b> <code>{}</code>".format(
                html.escape(_truncate_head(str(k), MAX_CONTEXT_VALUE_CHARS)),
                html.escape(_truncate_head(str(v), MAX_CONTEXT_VALUE_CHARS)),
            )
            for k, v in context.items()
        )
        context_block = f"\n{rendered}\n"

    try:
        exc_message = str(exc)
    except Exception:
        # a broken __str__ must not defeat the report
        exc_message = repr(exc)

    message = ERROR_MESSAGE.format(
        location=html.escape(_truncate_head(location, MAX_CONTEXT_VALUE_CHARS)),
        exc_type=html.escape(type(exc).__name__),
        exc_message=html.escape(
            _truncate_head(exc_message, MAX_EXC_MESSAGE_CHARS) or "—"
        ),
        context=context_block,
        traceback=html.escape(_truncate_tail(tb, MAX_TRACEBACK_CHARS)),
    )

    if len(message) > MAX_MESSAGE_CHARS:
        # backstop: HTML-escaping can still inflate a capped string past the
        # limit. Cut inside the <pre> block so the markup stays balanced.
        overflow = len(message) - MAX_MESSAGE_CHARS
        message = message[: -(overflow + len("</pre>") + 4)] + "...</pre>"

    return message


@app.task(name="app.services.error_service.send_error_to_developer")
def send_error_to_developer(text):
    """Deliver an already-rendered error report over the newsletter endpoint.

    Deliberately swallows its own failures: `send_newsletter` raises when the
    bot process is unreachable, and reporting that would recurse straight back
    into here. A lost alert is better than an alert loop.
    """
    if not DEVELOPER_USER_ID:
        return

    # imported here so a circular import can never break the reporting path
    from app.services.notification_service import send_newsletter

    try:
        send_newsletter(DEVELOPER_USER_ID, text)
    except Exception:
        logger.exception("Failed to deliver an error report to the developer")


# marks an exception object as already reported, so a failure bubbling up
# through several decorated frames is only sent once — from the innermost one
_REPORTED_FLAG = "_developer_notified"


def report_exception(exc, location, context=None):
    """Send one exception to the developer. Never raises.

    Call this from an `except` block when you want to alert but keep handling
    the error yourself. Use `@notify_on_exception` when the exception should
    simply propagate after being reported.
    """
    try:
        if not DEVELOPER_USER_ID:
            return
        if getattr(exc, _REPORTED_FLAG, False):
            return
        try:
            setattr(exc, _REPORTED_FLAG, True)
        except Exception:
            # some exception types don't accept new attributes; fall through
            # to the fingerprint check, which still limits the damage
            pass
        if not _should_send(location, exc):
            return

        text = build_error_message(location, exc, context)
        try:
            send_error_to_developer.delay(text)
        except Exception:
            # broker down — fall back to reporting synchronously
            send_error_to_developer(text)
    except Exception:
        # reporting must never mask or replace the original failure
        pass


def notify_on_exception(_func=None, *, location=None, reraise=True, default=None):
    """Report any exception raised by the wrapped function to the developer.

    By default the exception is re-raised, so behaviour is unchanged and only
    the alert is added. Pass ``reraise=False`` to swallow it and return
    ``default`` instead — for callers that must keep going, such as a loop over
    clients where one bad client should not abort the whole run.
    """

    def decorator(func):
        name = location or f"{func.__module__}.{func.__qualname__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                report_exception(exc, name)
                if reraise:
                    raise
                return default

        return wrapper

    if _func is not None:
        return decorator(_func)
    return decorator
