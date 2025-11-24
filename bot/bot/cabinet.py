from bot.bot import *
from bot.models import Cabinet
from app.models import Client


async def _to_the_selecting_cabinet(update: Update, context: CustomContext) -> int:
    bot_user = await Bot_user.objects.aget(user_id=update.effective_message.chat.id)
    current_cabinet = await bot_user.get_active_cabinet()
    current_client = await current_cabinet.get_client
    keyboards = [
        [
            InlineKeyboardButton(
                text=f"{client.name}",
                callback_data=f"switch_to-{client.id}"
            )
        ] async for client in Client.objects.filter(phone=current_client.phone).exclude(id = current_client.id)

    ]
    keyboards.append([
        InlineKeyboardButton(
            text=context.words.main_menu,
            callback_data="main_menu"
        )

    ]
    )
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
    # de activate all cabinets of the user
    await Cabinet.objects.all().aupdate(is_active=False)
    # get or create new cabinet by client
    bot_user: Bot_user = await get_object_by_update(update)
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