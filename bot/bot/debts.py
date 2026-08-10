from bot.bot import *
import asyncio
from bot.models import *
from app.models import Client
from app.services.smartup_service import SmartUpApiClient, ApiMethods
from bot.services.string_service import debts_history_string, debts_history_rich_html


async def _client_debts(update: Update, context: CustomContext):
    await update.callback_query.edit_message_reply_markup(None)

    cabinet: Cabinet = await (await get_object_by_update(update)).get_active_cabinet
    client: Client = await cabinet.get_client

    context.application.create_task(
        _send_client_debts_in_background(
            context=context,
            chat_id=update.effective_chat.id,
            client_external_id=client.external_id,
        )
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.debts_loading,
        parse_mode="HTML"
    )

    return ConversationHandler.END


async def _send_client_debts_in_background(context: CustomContext, chat_id: int, client_external_id: str):
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

    smartup_client = SmartUpApiClient(ApiMethods.debts_list)
    debts = await asyncio.to_thread(smartup_client.get_debts_by_client, client_external_id)
    rich_tables = await debts_history_rich_html(context, debts)

    if rich_tables:
        try:
            menu_markup = (await main_menu_keyboard(context)).to_dict()
            for i, html in enumerate(rich_tables):
                is_last = i == len(rich_tables) - 1
                payload = {
                    "chat_id": chat_id,
                    "rich_message": {"html": html},
                }
                if is_last:
                    payload["reply_markup"] = menu_markup

                await context.bot._post(
                    "sendRichMessage",
                    data=payload,
                )
            return ConversationHandler.END
        except Exception:
            pass

    text_messages = await debts_history_string(context, debts)
    for i, text in enumerate(text_messages):
        is_last = i == len(text_messages) - 1
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML",
            reply_markup=await main_menu_keyboard(context) if is_last else None
        )
