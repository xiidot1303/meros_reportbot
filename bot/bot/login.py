from bot.bot import *
from app.models import Client
from bot.models import Bot_user

async def get_lang(update: Update, context: CustomContext) -> str:
    """Get user's language preference from the database."""
    text = update.effective_message.text
    # register client
    if "UZ" in text:
        lang = 0
    elif "RU" in text:
        lang = 1

    bot_user, is_created = await Bot_user.objects.aget_or_create(
        user_id = update.effective_message.chat.id,
    )
    bot_user.lang = lang
    await bot_user.asave()

    # check is user in clients list
    if client := await Client.objects.filter(tg_id=update.message.chat.id).afirst():
        # successfully resgistered
        text = context.words.successfully_registered
        client.bot_user = bot_user
        await client.asave()
    else:
        # user is not in clients list
        text = context.words.you_are_not_registered
    await update.message.reply_text(
        text=text,
        parse_mode=ParseMode.HTML
    )
    await main_menu(update, context)
    return ConversationHandler.END