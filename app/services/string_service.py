from bot.resources.strings import Strings
from app.models import Order, OrderTransport
from bot.models import Bot_user, Cabinet
from app.services import *


def order_status_change_string(order: Order, bot_user: Bot_user = None) -> str:
    if bot_user:
        lang = bot_user.lang
    else:
        lang = 0
    status_code = order.status
    text = (
        f"""{Strings.new_order[lang] if status_code == 'B#N' else 
           (Strings.order_status_changed_to[lang] + "<i>" + Order.get_status_label(status_code) + "</i>")}\n""" \
        f"{Strings.order_info[lang]}".format(
            deal_datetime = order.deal_datetime.strftime("%d.%m.%Y %H:%M:%S"),
            manager = order.manager,
            total_amount = format_number(order.total_amount),
            tin = order.tin
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
            deal_datetime = order.deal_datetime.strftime("%d.%m.%Y %H:%M:%S"),
            manager = order.manager,
            total_amount =  f"{format_number(old_price)} -> {format_number(new_price)}",
            tin = order.tin
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
    )
