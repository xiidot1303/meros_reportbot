from bot.bot import *
from app.models import Client
from bot.models import Bot_user


async def _to_the_getting_contact_via_button(update: Update, context: CustomContext) -> int:
    if update.callback_query:
        await update.callback_query.edit_message_reply_markup(None)
    """Go to getting contact via button state."""
    keyboard = [
        [
            KeyboardButton(
                text=context.words.leave_number, request_contact=True)
        ]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await update.effective_message.reply_text(
        text=context.words.please_send_your_contact_via_button,
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )
    return GET_CONTACT_VIA_BUTTON


async def _to_the_getting_phone_number(update: Update, context: CustomContext) -> int:
    """Go to getting phone number state."""
    await update.effective_message.reply_text(
        text=context.words.send_phone_number,
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=context.words.back,
                        callback_data="back",
                    )
                ]
            ]
        ),
        parse_mode=ParseMode.HTML
    )
    return GET_PHONE_NUMBER


async def _to_the_selecting_branch(update: Update, context: CustomContext) -> int:
    """Go to selecting branch state."""
    phone = context.user_data["phone_number"]
    # get client
    # build keyboard with branches
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=client.name,
                    callback_data=f"{client.id}"
                ) 
            ] async for client in Client.objects.filter(phone__icontains=phone)
        ]
    )
    await update.message.reply_text(
        text=context.words.please_select_your_branch,
        reply_markup=markup,
        parse_mode=ParseMode.HTML
    )
    return GET_BRANCH


#########################################################################################################################
#########################################################################################################################
#########################################################################################################################


async def get_lang(update: Update, context: CustomContext) -> str:
    """Get user's language preference from the database."""
    data = update.callback_query.data
    # register client
    if data == "uz":
        lang = 0
    elif data == "ru":
        lang = 1

    bot_user, is_created = await Bot_user.objects.aget_or_create(
        user_id=update.effective_message.chat.id,
    )
    bot_user.lang = lang
    await bot_user.asave()
    return await _to_the_getting_contact_via_button(update, context)


async def get_contact_via_button(update: Update, context: CustomContext) -> int:
    """Get user's contact via button."""
    contact = update.effective_message.contact
    # remove keyboard
    await update.effective_message.reply_text(
        text="✅",
        reply_markup = await reply_keyboard_remove()
    )
    # search client by phone number
    if await Client.objects.filter(phone__icontains=contact.phone_number).aexists():
        context.user_data["phone_number"] = contact.phone_number
        return await _to_the_selecting_branch(update, context)
    else:
        # user is not in clients list
        text = context.words.send_phone_number
        return await _to_the_getting_phone_number(update, context)


async def get_phone_number(update: Update, context: CustomContext) -> int:
    """Get user's phone number."""
    phone_number = update.effective_message.text.strip()
    # search client by phone number
    if await Client.objects.filter(phone__icontains=phone_number).aexists():
        context.user_data["phone_number"] = phone_number
        return await _to_the_selecting_branch(update, context)
    else:
        # user is not in clients list
        text = context.words.send_phone_number
        await update.effective_message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=context.words.back,
                            callback_data="back",
                        )
                    ]
                ]
            ),
            parse_mode=ParseMode.HTML
        )
        return


async def get_branch(update: Update, context: CustomContext) -> int:
    """Get user's branch."""
    branch_id = int(update.callback_query.data)
    client = await Client.objects.aget(id=branch_id)
    # register bot user
    bot_user: Bot_user = await get_object_by_update(update)
    cabinet, is_created = await Cabinet.objects.aget_or_create(
        bot_user=bot_user,
        client=client,
        is_active=True,
    )

    await main_menu(update, context)

    return ConversationHandler.END
