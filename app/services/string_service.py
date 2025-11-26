from bot.resources.strings import Strings
from app.models import Order
from bot.models import Bot_user, Cabinet

def order_status_change_string(order: Order, bot_user: Bot_user = None) -> str:
    if bot_user:
        lang = bot_user.lang
    else:
        lang = 0
    status_code = order.status
    text = (
        f"""{Strings.new_order[lang] if status_code == 'B#N' else 
           (Strings.order_status_changed_to[lang] + Order.get_status_label(status_code))}\n\n""" \
        f"{Strings.order_info[lang]}".format(
            delivery_date = order.delivery_date,
            manager = order.manager,
            total_amount = order.total_amount,
            tin = order.tin
        )
        )
    
    return text