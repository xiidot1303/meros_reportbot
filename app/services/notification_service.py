from app.models import Order
from app.services.string_service import *
import requests
from config import WEBHOOK_URL
from bot.models import Bot_user


def order_status_change_notify(order: Order):
    status = order.status
    text = order_status_change_string(order)
    bot_user: Bot_user = order.client.bot_user if order.client else None
    # send notification to user
    requests.post(
        url=f"{WEBHOOK_URL}/send-newsletter",
        json={
            "user_id": bot_user.user_id,
            "text": text
        }
    )