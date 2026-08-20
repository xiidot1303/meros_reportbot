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
    main, login, reconciliation_act, cabinet, orders, facturas, feedback
)

exceptions_for_filter_text = (~filters.COMMAND) & (
    ~filters.Text(Strings.main_menu))

login_handler = ConversationHandler(
    entry_points=[
        CommandHandler("start", main.start),
        CallbackQueryHandler(main.start, pattern="main_menu"),
    ],
    states={
        SELECT_LANG: [
            CallbackQueryHandler(login.get_lang, pattern="^(uz|ru)$")
        ],
        GET_CONTACT_VIA_BUTTON: [
            MessageHandler(
                filters.CONTACT,
                login.get_contact_via_button
            ),
            CallbackQueryHandler(
                main.main_menu,
                pattern="^back$"
            )
        ],
        GET_PHONE_NUMBER: [
            MessageHandler(
                exceptions_for_filter_text & filters.TEXT,
                login.get_phone_number
            ),
            CallbackQueryHandler(
                login._to_the_getting_contact_via_button,
                pattern="^back$"
            )
        ],
        GET_BRANCH: [
            CallbackQueryHandler(
                login.get_branch,
                pattern="^\d+$"
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


cabinet_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            callback=main.switch_cabinet,
            pattern="switch_cabinet",
        )
    ],
    states={
        SELECT_CABINET: [
            CallbackQueryHandler(
                cabinet.get_cabinet,
                pattern="^switch_to-\d+$"
            ),
            CallbackQueryHandler(
                cabinet.sign_out,
                pattern="^sign_out$"
            ),
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            callback=main.main_menu,
            pattern="^main_menu$",
        ),
        CommandHandler('start', main.main_menu)
    ],
    allow_reentry=True,
    persistent=True,
    name="cabinet_handler",
)


orders_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(main.orders_history, pattern="^order_history$")
    ],
    states={
        LOAD_MORE_ORDERS: [
            CallbackQueryHandler(orders.show_completed_orders, pattern="^show_completed_orders$"),
            CallbackQueryHandler(orders.load_more_orders, pattern="^load_more_orders$")
        ]
    },
    fallbacks=[
        CallbackQueryHandler(
            callback=main.main_menu,
            pattern="^main_menu$",
        ),
        CommandHandler('start', main.main_menu)
    ],
    allow_reentry=True,
    persistent=True,
    name="orders_handler"
)


debts_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(main.client_debts, pattern="^client_debts$")
    ],
    states={},
    fallbacks=[
        CallbackQueryHandler(
            callback=main.main_menu,
            pattern="^main_menu$",
        ),
        CommandHandler('start', main.main_menu)
    ],
    allow_reentry=True,
    persistent=True,
    name="debts_handler"
)


facturas_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(main.client_facturas, pattern="^facturas$")
    ],
    states={},
    fallbacks=[
        CallbackQueryHandler(
            callback=main.main_menu,
            pattern="^main_menu$",
        ),
        CommandHandler('start', main.main_menu)
    ],
    allow_reentry=True,
    persistent=True,
    name="facturas_handler"
)


feedback_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(main.feedback, pattern="^feedback$")
    ],
    states={
        GET_FEEDBACK_TTN: [
            MessageHandler(
                exceptions_for_filter_text & filters.TEXT,
                feedback.get_ttn
            )
        ],
        GET_FEEDBACK_TEXT: [
            MessageHandler(
                exceptions_for_filter_text & filters.TEXT,
                feedback.get_text
            )
        ],
        GET_FEEDBACK_FILE: [
            CallbackQueryHandler(
                feedback.skip_file,
                pattern="^feedback_skip_file$"
            ),
            MessageHandler(
                (~filters.COMMAND) & (
                    filters.PHOTO | filters.VIDEO | filters.Document.ALL
                    | filters.AUDIO | filters.VOICE | filters.ANIMATION
                ),
                feedback.get_file
            ),
            MessageHandler(
                exceptions_for_filter_text & filters.TEXT,
                feedback.get_file
            ),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(
            callback=main.main_menu,
            pattern="^main_menu$",
        ),
        CommandHandler('start', main.main_menu)
    ],
    allow_reentry=True,
    persistent=True,
    name="feedback_handler",
)


# the ТТН search behind the feedback form's "find ТТН" button
feedback_inline_query_handler = InlineQueryHandler(feedback.ttn_inline_query)


# admins answer client feedback by replying to the group message with "@@@"
admin_feedback_reply_handler = MessageHandler(
    filters.ChatType.GROUPS & filters.REPLY & (~filters.COMMAND),
    feedback.admin_group_reply,
)


handlers = [
    login_handler,
    reconciliation_act_handler,
    cabinet_handler,
    orders_handler,
    debts_handler,
    facturas_handler,
    feedback_handler,

    feedback_inline_query_handler,

    TypeHandler(type=NewsletterUpdate, callback=main.newsletter_update),

    admin_feedback_reply_handler,
]
