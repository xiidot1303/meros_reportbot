from bot.bot import *
from bot.models import Cabinet
from app.models import Client
from bot.services.access_service import accessible_clients_async, has_access_async


async def _to_the_selecting_cabinet(update: Update, context: CustomContext) -> int:
    bot_user = await Bot_user.objects.aget(user_id=update.effective_message.chat.id)
    current_cabinet = await bot_user.get_active_cabinet
    current_client = await current_cabinet.get_client()
    # owned clients and staffed ones alike, minus the one already open
    clients = (await accessible_clients_async(bot_user.phone)).exclude(
        id=current_client.id)
    keyboards = [
        [
            InlineKeyboardButton(
                text=f"{client.name}",
                callback_data=f"switch_to-{client.id}"
            )
        ] async for client in clients

    ]
    keyboards.append([
        InlineKeyboardButton(
            text=context.words.main_menu,
            callback_data="main_menu"
        )
    ])
    keyboards.append([
        InlineKeyboardButton(
            text=context.words.sign_out,
            callback_data="sign_out"
        )
    ])
    markup = InlineKeyboardMarkup(
        keyboards
    )

    await update.callback_query.edit_message_text(
        context.words.select_cabinet,
        reply_markup=markup
    )

    return SELECT_CABINET


async def get_cabinet(update: Update, context: CustomContext) -> Cabinet:
    """Get active cabinet of the user."""
    # get client id from callback data
    client_id = int(update.callback_query.data.split("-")[-1])
    client: Client = await Client.objects.aget(id=client_id)
    bot_user: Bot_user = await get_object_by_update(update)
    # a staff grant may have been revoked since this keyboard was drawn
    if not await has_access_async(bot_user.phone, client):
        await update.callback_query.answer(
            text=context.words.staff_access_revoked.format(client_name=client.name),
            show_alert=True
        )
        return await _to_the_selecting_cabinet(update, context)
    # de activate all cabinets of the user
    await Cabinet.objects.filter(bot_user=bot_user).aupdate(is_active=False)
    # get or create new cabinet by client
    cabinet, is_created = await Cabinet.objects.aget_or_create(
        bot_user=bot_user,
        client=client,
        defaults={'is_active': True},
    )
    if not is_created:
        cabinet.is_active = True
        await cabinet.asave()
    # answer callback query
    await update.callback_query.answer(
        text=context.words.cabinet_switched.format(client_name=client.name),
        show_alert=True
    )
    return await main_menu(update, context)


async def sign_out(update: Update, context: CustomContext):
    bot_user: Bot_user = await get_object_by_update(update)
    await Cabinet.objects.filter(bot_user=bot_user).adelete()
    await update.callback_query.answer(
        text=context.words.signed_out,
        show_alert=True
    )
    await update.callback_query.edit_message_text(context.words.signed_out)
    return ConversationHandler.END