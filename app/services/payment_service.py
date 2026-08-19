from datetime import datetime as dt
from decimal import Decimal, InvalidOperation

from app.services.notification_service import send_newsletter
from bot.models import Cabinet
from bot.resources.strings import Strings


DATETIME_FORMATS = (
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
    "%Y-%m-%d",
    "%d.%m.%Y",
)


def parse_datetime(value):
    if not value:
        return None
    if isinstance(value, dt):
        return value
    value = str(value).strip().replace("Z", "")
    for fmt in DATETIME_FORMATS:
        try:
            return dt.strptime(value, fmt)
        except ValueError:
            continue
    return None


def parse_amount(value):
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def format_amount(value):
    if value is None:
        return "0"
    return f"{value:,.2f}".replace(",", " ")


def format_datetime(value):
    if not value:
        return "-"
    return value.strftime("%d.%m.%Y %H:%M")


def notify_payment(tin, amount, datetime_value, purpose):
    """Send a "payment received" newsletter to every active cabinet of the client
    whose TIN matches the payment. Returns the number of notified users."""
    if not tin:
        return 0

    cabinets = Cabinet.objects.filter(
        client__tin=tin, is_active=True
    ).select_related("bot_user")

    notified = 0
    for cabinet in cabinets:
        bot_user = cabinet.bot_user
        if not bot_user or not bot_user.user_id:
            continue
        text = Strings(user_id=bot_user.user_id).payment_received.format(
            amount=format_amount(amount),
            datetime=format_datetime(datetime_value),
            purpose=purpose or "-",
        )
        send_newsletter(bot_user.user_id, text)
        notified += 1

    return notified
