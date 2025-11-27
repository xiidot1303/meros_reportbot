from bot.bot import *
from app.utils import *
from app.services.client_service import *
from app.services.smartup_service import *
from bot.models import Bot_user, Cabinet



async def get_start_date(update: Update, context: CustomContext):
    try:
        start_date = datetime.strptime(update.effective_message.text, "%d.%m.%Y")
    except ValueError:
        text = context.words.incorrect_date_format
        await update.effective_message.reply_text(text) 
        return
    
    context.user_data["reconciliation_act_start_date"] = update.effective_message.text

    text = context.words.enter_end_date
    # # remove inline buttons from current message
    # await update.callback_query.edit_message_reply_markup(reply_markup=None)
    await update.effective_message.reply_text(
        text=text,
        reply_markup = await main_menu_keyboard(context)
    )
    return GET_RECONCILIATION_END_DATE


async def get_end_date(update: Update, context: CustomContext):
    try:
        end_date = datetime.strptime(update.effective_message.text, "%d.%m.%Y")
    except ValueError:
        text = context.words.incorrect_date_format
        await update.effective_message.reply_text(text) 
        return
    
    start_date_t = context.user_data["reconciliation_act_start_date"]
    start_date = datetime.strptime(start_date_t, "%d.%m.%Y")

    # get current cabinet
    bot_user: Bot_user = await get_object_by_update(update)
    cabinet: Cabinet = await bot_user.get_active_cabinet
    client: Client = await cabinet.get_client
    smartup_client = SmartUpApiClient(ApiMethods.reconciliation_act_report)
    reconciliation_act_file_path = smartup_client.reconciliation_act_report(
        client_id=client.external_id,
        start_date=start_date, 
        end_date=end_date
    )
    await update.effective_message.reply_document(
        open(reconciliation_act_file_path, 'rb')
    )