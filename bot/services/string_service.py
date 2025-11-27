from bot.bot import *
from app.models import Order
from app.utils import format_number


async def order_info_string(context: CustomContext, order: Order):
    text = (
        f"{context.words.order_no} {order.deal_id}\n" \
        f"{context.words.order_info}".format(
            deal_datetime=order.deal_datetime.strftime("%d.%m.%Y %H:%M:%S"),
            manager=order.manager,
            total_amount=format_number(int(order.total_amount)),
            tin=order.tin,
        )
    )
    if order.status:
        text += f"\n{context.words.status}: {order.status}"

    return text
