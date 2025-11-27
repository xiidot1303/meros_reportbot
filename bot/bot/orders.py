from bot.bot import *
from bot.models import *
from app.models import Order, Client
from bot.services.string_service import *
from app.services.order_service import get_archived_orders_by_client
from bot.services.redis_service import redis_client


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
    text = await order_history_string(context, client)
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

    redis_client.set("next_offset", 0)
    context.job_queue.run_once(
        send_completed_orders_job,
        0,
        client.id,
        "send_completed_orders_job",
        update.effective_chat.id,
        update.effective_user.id
    )


    return LOAD_MORE_ORDERS


async def load_more_orders(update: Update, context: CustomContext):
    await update.callback_query.edit_message_reply_markup(None)
    # get current cabinet
    cabinet: Cabinet = await (await get_object_by_update(update)).get_active_cabinet
    client: Client = await cabinet.get_client

    context.job_queue.run_once(
        send_completed_orders_job,
        0,
        client.id,
        "send_completed_orders_job",
        update.effective_chat.id,
        update.effective_user.id
    )
    return


async def send_completed_orders_job(context: CustomContext):
    client_id = context.job.data
    client = await Client.objects.aget(pk=client_id)

    # get offset from user data
    offset = redis_client.get("next_offset").decode()
    text = await completed_orders_history_string(context, orders=await get_archived_orders_by_client(client, offset=offset))
    await context.bot.send_message(
        chat_id=context._chat_id,
        text=text,
        parse_mode="HTML"
    )

    await context.bot.send_message(
        chat_id=context._chat_id,
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

    redis_client.set("next_offset", int(offset) + 10)
