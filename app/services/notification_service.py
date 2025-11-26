from app.models import Order
from app.services.string_service import *
import requests
from config import WEBHOOK_URL
from bot.models import Bot_user, Cabinet


def order_status_change_notify(order: Order):
    text = order_status_change_string(order)
    for cabinet in Cabinet.objects.filter(client=order.client):
        bot_user: Bot_user = cabinet.bot_user
        # send notification to user
        requests.post(
            url=f"{WEBHOOK_URL}/send-newsletter",
            json={
                "user_id": bot_user.user_id,
                "text": text
            }
        )