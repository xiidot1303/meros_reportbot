from bot import *
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    InlineQueryHandler,
    TypeHandler,
    ConversationHandler
)

from bot.resources.conversationList import *

from bot.bot import (
    main, login, reconciliation_act
)

exceptions_for_filter_text = (~filters.COMMAND) & (
    ~filters.Text(Strings.main_menu))

login_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", main.start),
    ],
    states={
        SELECT_LANG: [
            MessageHandler(filters.Text("UZ 🇺🇿") |
                           filters.Text("RU 🇷🇺"), login.get_lang)
        ],
    },
    fallbacks=[],
    allow_reentry=True,
    persistent=True,
    name="login_handler",
)

reconciliation_act_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=main.reconciliation_act,
            pattern="reconciliation_act",
        )
    ],
    states={
        GET_RECONCILIATION_START_DATE: [
            MessageHandler(
                exceptions_for_filter_text & filters.TEXT,
                reconciliation_act.get_start_date
            )
        ],
        GET_RECONCILIATION_END_DATE: [
            MessageHandler(
                exceptions_for_filter_text & filters.TEXT,
                reconciliation_act.get_end_date
            )
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            callback=main.main_menu,
            pattern="^main_menu$",
        ),
        CommandHandler('start', main.main_menu)
    ],
    allow_reentry=False,
    persistent=True,
    name="reconciliation_act_handler",
    # per_message=True

)


handlers = [
    login_handler,
    reconciliation_act_handler,


    TypeHandler(type=NewsletterUpdate, callback=main.newsletter_update)
]
