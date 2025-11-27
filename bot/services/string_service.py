from bot.bot import *
from app.models import Order, Client
from app.utils import format_number


async def order_history_string(context: CustomContext, client: Client):
    result = ""
    async for order in Order.objects.filter(client=client):
        text = (
            f"{context.words.order_no} {order.deal_id}"
            f"{context.words.order_history_info}".format(
                delivery_date=order.delivery_date.strftime("%d.%m.%Y"),
                total_amount=format_number(round(float(order.total_amount)))
            )
        )
        if order.status:
            text += f"🔸 {context.words.status}: {Order.get_status_label(order.status)}"

        result += (
            f"{text}" \
            "\n\n➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        )

    return result


async def completed_orders_history_string(context: CustomContext, orders):
    result = ""
    for order in orders:
        text = (
            f"{context.words.order_no} {order.deal_id}"
            f"{context.words.order_history_info}".format(
                delivery_date=order.delivery_date.strftime("%d.%m.%Y"),
                total_amount=format_number(round(float(order.total_amount)))
            )
        )
        result += (
            f"{text}" \
            "\n➖➖➖➖➖➖➖➖➖➖➖➖➖➖➖\n\n"
        )

    return result
