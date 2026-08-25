import base64

from core.celery import app
from app.models import Order, OrderTransport
from app.services.string_service import *
from app.services.error_service import notify_on_exception, report_exception
import requests
from config import NEWSLETTER_URL
from bot.models import Bot_user, Cabinet
from app.services.smartup_service import SmartUpApiClient, ApiMethods


def send_newsletter(user_id, text):
    response = requests.post(
        url=f"{NEWSLETTER_URL}/send-newsletter/",
        json={
            "user_id": user_id,
            "text": text
        }
    )
    response.raise_for_status()

def send_newsletter_with_document(user_id, document, document_name="report.xlsx", text=None):
    payload = {
        "user_id": user_id,
        "document": base64.b64encode(document).decode("utf-8"),
        "document_name": document_name,
    }
    if text:
        payload["text"] = text
    response = requests.post(
        url=f"{NEWSLETTER_URL}/send-newsletter/",
        json=payload
    )
    response.raise_for_status()


def get_order_report_bytes(order: Order):
    smartup_client = SmartUpApiClient(ApiMethods.order_report_template)
    report_template_id = smartup_client.save_report_template(order.deal_id)
    return smartup_client.download_order_report(report_template_id)


def send_order_report_to_user(order: Order, bot_user: Bot_user):
    try:
        report_bytes = get_order_report_bytes(order)
    except Exception as exc:
        report_exception(
            exc,
            "app.services.notification_service.send_order_report_to_user",
            context={"deal_id": order.deal_id, "user_id": bot_user.user_id},
        )
        return

    if not report_bytes:
        return

    send_newsletter_with_document(
        bot_user.user_id,
        report_bytes,
        document_name=f"order_report_{order.deal_id}.xlsx",
    )


@app.task(name="app.services.notification_service.order_status_change_notify")
@notify_on_exception(reraise=False)
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
@notify_on_exception(reraise=False)
def order_price_change_notify(order_id, old_price, new_price):
    order: Order = Order.objects.get(pk=order_id)
    for cabinet in Cabinet.objects.filter(client=order.client):
        bot_user: Bot_user = cabinet.bot_user
        text = order_price_change_string(order, bot_user, old_price, new_price)
        send_newsletter(bot_user.user_id, text)


@app.task(name="app.services.notification_service.order_transport_notify")
@notify_on_exception(reraise=False)
def order_transport_notify(transport_id):
    transport: OrderTransport = OrderTransport.objects.filter(pk=transport_id).select_related("order").first()
    if not transport or not transport.order or not transport.order.client:
        return

    for cabinet in Cabinet.objects.filter(client=transport.order.client).select_related("bot_user"):
        bot_user: Bot_user = cabinet.bot_user
        if not bot_user or not bot_user.user_id:
            continue
        text = order_transport_string(transport, bot_user)
        send_newsletter(bot_user.user_id, text)
