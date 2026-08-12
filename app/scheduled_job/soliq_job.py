from datetime import timedelta

from django.utils import timezone

from app.models import Texture
from app.services.notification_service import send_newsletter, send_newsletter_with_document
from app.services.soliq_service import soliqRequest, download_factura_pdf
from bot.models import Cabinet


def _format_amount(value):
    if value is None:
        return "0"
    return format(float(value), ".2f")


def _client_factura_message(client, texture, lang=0):
    if lang == 0:
        return (
            f"<b>📄 Yangi factura qabul qilindi!</b>\n"
            f"<b>№:</b> <code>{texture.doc_no or texture.doc_id}</code>\n"
            f"<b>Sana:</b> <code>{texture.doc_date}</code>\n"
        )
    return (
        f"<b>📄 Получена новая фактура!</b>\n"
        f"<b>№:</b> <code>{texture.doc_no or texture.doc_id}</code>\n"
        f"<b>Дата:</b> <code>{texture.doc_date}</code>\n"
    )


def _client_factura_reminder(client, texture, lang=0):
    days = (timezone.now().date() - texture.doc_date).days if texture.doc_date else 0
    if lang == 0:
        return (
            f"⚠️ <b>Faktura {days} kun davomida qabul qilinmagan.</b>\n"
            f"<b>№:</b> <code>{texture.doc_no or texture.doc_id}</code>\n"
            f"<b>Sana:</b> <code>{texture.doc_date}</code>"
        )
    return (
        f"⚠️ <b>Счет-фактура не принята уже {days} дней.</b>\n"
        f"<b>№:</b> <code>{texture.doc_no or texture.doc_id}</code>\n"
        f"<b>Дата:</b> <code>{texture.doc_date}</code>"
    )


def _send_to_cabinet_users(client, message, lang=None):
    for cabinet in Cabinet.objects.filter(client=client, is_active=True).select_related("bot_user"):
        bot_user = cabinet.bot_user
        if not bot_user or not bot_user.user_id:
            continue
        send_newsletter(bot_user.user_id, message if lang is None else message)


def _fetch_documents_for_client(client):
    if not client or not client.tin:
        return []

    response = soliqRequest(
        "/api/v3/lists",
        {
            "method": "get",
            "params": [
                ("path", "sent"),
                ("offset", 0),
                ("limit", 100),
                ("docStatus", ""),
                ("folderId", 0),
                ("docType", "factura"),
                ("tin", client.tin),
                ("docStatus", "header_receive,pending"),
            ],
        },
    )
    if not isinstance(response, dict):
        return []
    return response.get("data", {}).get("documents", [])


def _notify_new_factura(client, texture):
    pdf_bytes = download_factura_pdf(texture.doc_id)
    
    for cabinet in Cabinet.objects.filter(client=client, is_active=True).select_related("bot_user"):
        bot_user = cabinet.bot_user
        if bot_user and bot_user.user_id:
            message = _client_factura_message(client, texture, lang=bot_user.lang or 0)
            if pdf_bytes:
                send_newsletter_with_document(
                    bot_user.user_id, 
                    pdf_bytes, 
                    document_name=f"factura_{texture.doc_no or texture.doc_id}.pdf",
                    text=message
                )
            else:
                send_newsletter(bot_user.user_id, message)
    texture.is_new_notified = True
    texture.save(update_fields=["is_new_notified"])


def _notify_reminder(client, texture):
    today = timezone.now().date()
    if not texture.doc_date:
        return

    if texture.last_reminder_sent_at and texture.last_reminder_sent_at.date() == today:
        return

    pdf_bytes = download_factura_pdf(texture.doc_id)

    for cabinet in Cabinet.objects.filter(client=client, is_active=True).select_related("bot_user"):
        bot_user = cabinet.bot_user
        if bot_user and bot_user.user_id:
            message = _client_factura_reminder(client, texture, lang=bot_user.lang or 0)
            if pdf_bytes:
                send_newsletter_with_document(
                    bot_user.user_id, 
                    pdf_bytes, 
                    document_name=f"factura_{texture.doc_no or texture.doc_id}.pdf",
                    text=message
                )
            else:
                send_newsletter(bot_user.user_id, message)

    texture.last_reminder_sent_at = timezone.now()
    texture.save(update_fields=["last_reminder_sent_at"])


def sync_facturas_for_active_cabinets():
    clients = []
    for cabinet in Cabinet.objects.filter(is_active=True).select_related("client"):
        client = cabinet.client
        if client and client.tin and client not in clients:
            clients.append(client)

    for client in clients:
        documents = _fetch_documents_for_client(client)
        for document in documents:
            texture, created = Texture.save_or_update_from_payload(document, client=client)
            if created:
                _notify_new_factura(client, texture)
                continue

            if texture.doc_date and timezone.now().date() - texture.doc_date >= timedelta(days=5):
                _notify_reminder(client, texture)
