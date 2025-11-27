from app.models import Order
from app.services.string_service import *
import requests
from config import WEBHOOK_URL
from bot.models import Bot_user, Cabinet


def send_newsletter(user_id, text):
    requests.post(
        url=f"{WEBHOOK_URL}/send-newsletter/",
        json={
            "user_id": user_id,
            "text": text
        }
    )


def order_status_change_notify(order: Order):
    for cabinet in Cabinet.objects.filter(client=order.client):
        bot_user: Bot_user = cabinet.bot_user
        text = order_status_change_string(order, bot_user)
        # send notification to user
        send_newsletter(bot_user.user_id, text)


def order_price_change_notify(order: Order, old_price):
    for cabinet in Cabinet.objects.filter(client=order.client):
        bot_user: Bot_user = cabinet.bot_user
        text = order_price_change_string(order, bot_user, old_price)
        send_newsletter(bot_user.user_id, text)
