import base64

from core.celery import app
from app.models import Order
from app.services.string_service import *
import requests
from config import NEWSLETTER_URL
from bot.models import Bot_user, Cabinet
from app.services.smartup_service import SmartUpApiClient, ApiMethods


def send_newsletter(user_id, text):
    requests.post(
        url=f"{NEWSLETTER_URL}/send-newsletter/",
        json={
            "user_id": user_id,
            "text": text
        }
    )

def send_newsletter_with_document(user_id, document, document_name="report.xlsx", text=None):
    payload = {
        "user_id": user_id,
        "document": base64.b64encode(document).decode("utf-8"),
        "document_name": document_name,
    }
    if text:
        payload["text"] = text
    requests.post(
        url=f"{NEWSLETTER_URL}/send-newsletter/",
        json=payload
    )


def get_order_report_bytes(order: Order):
    smartup_client = SmartUpApiClient(ApiMethods.order_report_template)
    report_template_id = smartup_client.save_report_template(order.deal_id)
    return smartup_client.download_order_report(report_template_id)


def send_order_report_to_user(order: Order, bot_user: Bot_user):
    try:
        report_bytes = get_order_report_bytes(order)
    except Exception:
        return

    if not report_bytes:
        return

    send_newsletter_with_document(
        bot_user.user_id,
        report_bytes,
        document_name=f"order_report_{order.deal_id}.xlsx",
    )


@app.task(name="app.services.notification_service.order_status_change_notify")
def order_status_change_notify(order_id=None, order_deal_id=None):
    if order_deal_id:
        order: Order = Order.objects.filter(deal_id = order_deal_id).first()
    else:
        order: Order = Order.objects.get(pk = order_id)


    for cabinet in Cabinet.objects.filter(client=order.client):
        bot_user: Bot_user = cabinet.bot_user
        text = order_status_change_string(order, bot_user)
        # send notification to user
        send_newsletter(bot_user.user_id, text)
        if order.status == "A":
            send_order_report_to_user(order, bot_user)


@app.task(name="app.services.notification_service.order_price_change_notify")
def order_price_change_notify(order_id, old_price):
    order: Order = Order.objects.get(pk=order_id)
    for cabinet in Cabinet.objects.filter(client=order.client):
        bot_user: Bot_user = cabinet.bot_user
        text = order_price_change_string(order, bot_user, old_price)
        send_newsletter(bot_user.user_id, text)
