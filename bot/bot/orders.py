from bot.bot import *
from bot.models import *
from app.models import Order, Client
from bot.services.string_service import *
from app.services.order_service import get_archived_orders_by_client


async def _orders_list(update: Update, context: CustomContext):
    await update.callback_query.edit_message_reply_markup(None)
    await update.effective_message.reply_chat_action(action=ChatAction.TYPING)
    # get current cabinet
    cabinet: Cabinet = await (await get_object_by_update(update)).get_active_cabinet
    client: Client = await cabinet.get_client

    # send active orders list
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.active_orders,
        parse_mode="HTML"
    )
    async for order in Order.objects.filter(client=client):
        text = await order_info_string(context, order)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="HTML"
        )

    # send completed orders list
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.completed_orders,
        parse_mode="HTML"
    )

    for order in await get_archived_orders_by_client(client):
        text = await order_info_string(context, order)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="HTML"
        )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.you_can_continue_or_return,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=context.words.load_more_orders,
                        callback_data="load_more_orders"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=context.words.main_menu,
                        callback_data="main_menu"
                    )

                ]
            ]
        )
    )

    context.user_data['next_offset'] = 10

    return LOAD_MORE_ORDERS


async def load_more_orders(update: Update, context: CustomContext):
    await update.callback_query.edit_message_reply_markup(None)
    # get current cabinet
    cabinet: Cabinet = await (await get_object_by_update(update)).get_active_cabinet
    client: Client = await cabinet.get_client

    # get offset from user data
    offset = context.user_data['next_offset']
    for order in await get_archived_orders_by_client(client, offset=offset):
        text = await order_info_string(context, order)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=text,
            parse_mode="HTML"
        )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=context.words.you_can_continue_or_return,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=context.words.load_more_orders,
                        callback_data="load_more_orders"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=context.words.main_menu,
                        callback_data="main_menu"
                    )

                ]
            ]
        )
    )

    context.user_data['next_offset'] += 10
