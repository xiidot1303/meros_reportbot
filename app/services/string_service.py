from bot.resources.strings import Strings
from app.models import Order, OrderTransport
from bot.models import Bot_user, Cabinet
from app.services import *


def _format_date(value) -> str:
    """A date as the client expects to see it, or a dash when unset."""
    if not value:
        return "—"
    return value.strftime("%d.%m.%Y")


def _delivery_date(order: Order) -> str:
    """The shipping date as the client expects to see it.

    `delivery_date` is nullable, so orders that have not been scheduled yet
    render a dash rather than raising.
    """
    return _format_date(order.delivery_date)


# What each status actually means to the client, rather than its raw label.
# A status missing here falls back to the generic "status changed to <label>".
_STATUS_HEADERS = {
    "B#N": "new_order",                 # a brand new sale
    "B#W": "order_status_waiting",      # finance department approved it
    "B#S": "order_status_shipped",      # warehouse started assembling the goods
    "B#V": "order_status_delivered",    # warehouse finished preparing the goods
    "A": "order_status_archived",       # SmartUp/Soliq facturas were sent
}


def _status_header(status_code, lang) -> str:
    """The headline for a status change, in the user's language."""
    key = _STATUS_HEADERS.get(status_code)
    if key:
        return getattr(Strings, key)[lang]

    # unknown status: fall back to naming it outright
    label = Order.get_status_label(status_code) or status_code or "—"
    return Strings.order_status_changed_to[lang] + "<i>" + label + "</i>"


def order_status_change_string(order: Order, bot_user: Bot_user = None) -> str:
    if bot_user:
        lang = bot_user.lang
    else:
        lang = 0

    text = (
        f"{_status_header(order.status, lang)}\n" \
        f"{Strings.order_info[lang]}".format(
            delivery_number = order.delivery_number or "—",
            delivery_date = _delivery_date(order),
            sales_manager_name = order.sales_manager_name or "—",
            total_amount = format_number(order.total_amount),
        )
        )

    return text

def order_price_change_string(order: Order, bot_user: Bot_user, old_price, new_price):
    if bot_user:
        lang = bot_user.lang
    else:
        lang = 0

    status_code = order.status
    
    text = (
        f"""{Strings.order_price_changed[lang]}\n""" \
        f"{Strings.order_info[lang]}".format(
            delivery_number = order.delivery_number or "—",
            delivery_date = _delivery_date(order),
            sales_manager_name = order.sales_manager_name or "—",
            total_amount =  f"{format_number(old_price)} -> {format_number(new_price)}",
        )
        )
    
    return text

def order_delivery_date_change_string(order: Order, bot_user: Bot_user, old_date, new_date):
    """Message for a rescheduled shipment, showing the old and new dates."""
    if bot_user:
        lang = bot_user.lang
    else:
        lang = 0

    text = (
        f"""{Strings.order_delivery_date_changed[lang]}""".format(
            old_date=_format_date(old_date),
            new_date=_format_date(new_date),
        ) + "\n"
        f"{Strings.order_info[lang]}".format(
            delivery_number = order.delivery_number or "—",
            delivery_date = _delivery_date(order),
            sales_manager_name = order.sales_manager_name or "—",
            total_amount = format_number(order.total_amount),
        )
        )

    return text


def order_transport_string(transport: OrderTransport, bot_user: Bot_user = None) -> str:
    """Message for a freshly registered transport — the cargo is loaded and moving."""
    user_id = bot_user.user_id if bot_user else None

    return Strings(user_id=user_id).order_transport_on_the_way.format(
        order_no=transport.order.deal_id if transport.order else transport.order_id_external,
        car_name=transport.car_name or "—",
        car_autonum=transport.car_autonum or "—",
        driver_name=transport.driver_name or "—",
        phone_number=transport.phone_number or "—",
        box_count=transport.box_count or "—",
        price=transport.price or "—",
    )
