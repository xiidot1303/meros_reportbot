import asyncio
import io

from bot.bot import *
from bot.models import Cabinet
from app.models import Client


async def _client_facturas(update: Update, context: CustomContext):
    await update.callback_query.edit_message_reply_markup(None)

    cabinet: Cabinet = await (await get_object_by_update(update)).get_active_cabinet
    client: Client = await cabinet.get_client()

    context.application.create_task(
        _send_client_facturas_in_background(
            context=context,
            chat_id=update.effective_chat.id,
            client_id=client.id,
        )
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.facturas_loading,
        parse_mode="HTML"
    )

    return ConversationHandler.END


def _collect_facturas(client_id):
    """Fetch unaccepted facturas from Soliq and upsert them; runs in a worker thread."""
    from app.models import Texture
    from app.services.soliq_service import fetch_pending_documents

    client = Client.objects.get(pk=client_id)
    documents = fetch_pending_documents(client)

    facturas = []
    for document in documents:
        texture, _ = Texture.save_or_update_from_payload(document, client=client)
        if texture:
            facturas.append(texture)
    return facturas


async def _send_client_facturas_in_background(context: CustomContext, chat_id: int, client_id: int):
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    try:
        facturas = await asyncio.to_thread(_collect_facturas, client_id)
    except Exception:
        await context.bot.send_message(
            chat_id=chat_id,
            text=context.words.facturas_error,
            parse_mode="HTML",
            reply_markup=await main_menu_keyboard(context),
        )
        return

    if not facturas:
        await context.bot.send_message(
            chat_id=chat_id,
            text=context.words.no_facturas_found,
            parse_mode="HTML",
            reply_markup=await main_menu_keyboard(context),
        )
        return

    await context.bot.send_message(
        chat_id=chat_id,
        text=context.words.facturas_found.format(count=len(facturas)),
        parse_mode="HTML"
    )

    await _send_factura_documents(context, chat_id, facturas)


async def _send_factura_documents(context: CustomContext, chat_id: int, facturas):
    from app.services.soliq_service import download_factura_pdf

    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)

    for i, texture in enumerate(facturas):
        is_last = i == len(facturas) - 1
        reply_markup = await main_menu_keyboard(context) if is_last else None
        doc_no = texture.doc_no or texture.doc_id

        pdf_bytes = await asyncio.to_thread(download_factura_pdf, texture.doc_id)
        if not pdf_bytes:
            await context.bot.send_message(
                chat_id=chat_id,
                text=context.words.factura_download_failed.format(doc_no=doc_no),
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
            continue

        document = io.BytesIO(pdf_bytes)
        document.name = f"factura_{doc_no}.pdf"
        await context.bot.send_document(
            chat_id=chat_id,
            document=document,
            caption=context.words.factura_document.format(
                doc_no=doc_no,
                doc_date=texture.doc_date,
            ),
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
