from bot.bot import *
from app.models import Client
from bot.models import Bot_user, Cabinet, ClientStaff
from bot.services.access_service import (
    is_owner_async, normalize_phone, phone_tail, revoke_staff_async,
)
from asgiref.sync import sync_to_async


@sync_to_async
def _staff_rows(client):
    return list(ClientStaff.objects.filter(client=client).order_by("date"))


@sync_to_async
def _add_staff(client, phone, bot_user):
    """Create the grant, plus a cabinet if the staff member already uses the bot.

    Creating the cabinet up front is what makes the client show up in their
    list without a re-login — and it is also what subscribes them to the
    client's notifications, which iterate over `Cabinet` rows.
    """
    staff, created = ClientStaff.objects.get_or_create(
        client=client, phone=phone, defaults={"added_by": bot_user})
    if not created:
        return staff, False, None

    tail = phone_tail(phone)
    notified = None
    for existing in Bot_user.objects.filter(phone__endswith=tail):
        Cabinet.objects.get_or_create(
            bot_user=existing, client=client, defaults={"is_active": False})
        if existing.user_id:
            notified = existing.user_id
    return staff, True, notified


@sync_to_async
def _staff_user_ids(client, phone):
    tail = phone_tail(phone)
    return [
        user_id for user_id in Bot_user.objects.filter(
            phone__endswith=tail).values_list("user_id", flat=True)
        if user_id
    ]


async def _to_the_staff_list(update: Update, context: CustomContext) -> int:
    """Show the staff of the active cabinet's client, with a delete button each."""
    bot_user: Bot_user = await get_object_by_update(update)
    cabinet: Cabinet = await bot_user.get_active_cabinet
    client = await cabinet.get_client()

    if not await is_owner_async(bot_user.phone, client):
        await update.callback_query.answer(
            text=context.words.staff_not_owner, show_alert=True)
        return await main_menu(update, context)

    context.user_data["staff_client_id"] = client.id

    rows = await _staff_rows(client)
    keyboards = [
        [
            InlineKeyboardButton(
                text=f"❌ {row.phone}" + (f" — {row.name}" if row.name else ""),
                callback_data=f"staff_remove-{row.id}"
            )
        ] for row in rows
    ]
    keyboards.append([
        InlineKeyboardButton(
            text=context.words.staff_add, callback_data="staff_add")
    ])
    keyboards.append([
        InlineKeyboardButton(
            text=context.words.main_menu, callback_data="main_menu")
    ])

    text = (
        context.words.staff_list_title if rows else context.words.staff_list_empty
    ).format(client_name=client.name)

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(keyboards),
            parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboards),
            parse_mode=ParseMode.HTML)

    return STAFF_LIST


#########################################################################################################################
#########################################################################################################################
#########################################################################################################################


async def staff_add(update: Update, context: CustomContext) -> int:
    """Ask the owner for the phone number to grant."""
    keyboard = [
        [KeyboardButton(text=context.words.leave_number, request_contact=True)]
    ]
    await update.callback_query.edit_message_reply_markup(None)
    await update.effective_message.reply_text(
        text=context.words.staff_ask_phone,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=keyboard, resize_keyboard=True, one_time_keyboard=True),
        parse_mode=ParseMode.HTML
    )
    return GET_STAFF_PHONE


async def get_staff_phone(update: Update, context: CustomContext) -> int:
    """Register the phone the owner sent, by text or by shared contact."""
    if update.effective_message.contact:
        raw_phone = update.effective_message.contact.phone_number
        raw_name = " ".join(filter(None, [
            update.effective_message.contact.first_name,
            update.effective_message.contact.last_name,
        ]))
    else:
        raw_phone = update.effective_message.text
        raw_name = ""

    phone = normalize_phone(raw_phone)
    if not phone:
        await update.effective_message.reply_text(
            text=context.words.staff_phone_invalid, parse_mode=ParseMode.HTML)
        return GET_STAFF_PHONE

    client = await Client.objects.aget(id=context.user_data["staff_client_id"])

    # remove the contact-request keyboard now that we have a usable number
    await update.effective_message.reply_text(
        text="✅", reply_markup=await reply_keyboard_remove())

    if await is_owner_async(phone, client):
        await update.effective_message.reply_text(
            text=context.words.staff_is_owner.format(phone=phone),
            parse_mode=ParseMode.HTML)
        return await _to_the_staff_list(update, context)

    bot_user: Bot_user = await get_object_by_update(update)
    staff, created, notified_user_id = await _add_staff(client, phone, bot_user)

    if created:
        if raw_name:
            staff.name = raw_name
            await staff.asave()
        await update.effective_message.reply_text(
            text=context.words.staff_added.format(
                phone=phone, client_name=client.name),
            parse_mode=ParseMode.HTML)
        # tell the staff member the cabinet is theirs, if they already use the bot
        if notified_user_id:
            try:
                await context.bot.send_message(
                    chat_id=notified_user_id,
                    text=Strings(user_id=notified_user_id).staff_access_granted.format(
                        client_name=client.name),
                    parse_mode=ParseMode.HTML)
            except Exception:
                pass
    else:
        await update.effective_message.reply_text(
            text=context.words.staff_already_added.format(phone=phone),
            parse_mode=ParseMode.HTML)

    return await _to_the_staff_list(update, context)


async def staff_remove(update: Update, context: CustomContext) -> int:
    """Revoke a grant; the staff member's cabinet for this client goes with it."""
    staff_id = int(update.callback_query.data.split("-")[-1])
    staff = await ClientStaff.objects.filter(pk=staff_id).select_related("client").afirst()
    if not staff:
        return await _to_the_staff_list(update, context)

    client = staff.client
    phone = staff.phone
    user_ids = await _staff_user_ids(client, phone)

    await revoke_staff_async(client, phone)

    await update.callback_query.answer(
        text=context.words.staff_removed.format(phone=phone), show_alert=True)

    for user_id in user_ids:
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text=Strings(user_id=user_id).staff_access_revoked.format(
                    client_name=client.name),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass

    return await _to_the_staff_list(update, context)
