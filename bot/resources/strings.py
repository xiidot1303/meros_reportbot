

class Strings:
    def __init__(self, user_id) -> None:
        self.user_id = user_id

    def __getattribute__(self, key: str):
        if result := object.__getattribute__(self, key):
            if isinstance(result, list):
                from bot.services.redis_service import get_user_lang
                user_id = object.__getattribute__(self, "user_id")
                user_lang_code = get_user_lang(user_id)
                return result[user_lang_code]
            else:
                return result
        else:
            return key

    hello = """🤖 Xush kelibsiz!\n Bot tilini tanlang  🌎 \n\n ➖➖➖➖➖➖➖➖➖➖➖➖\n
    👋 Добро пожаловать \n \U0001F1FA\U0001F1FF Выберите язык бота \U0001F1F7\U0001F1FA"""
    added_group = "Чат успешно добавлена ✅"
    uz_ru = ["UZ 🇺🇿", "RU 🇷🇺"]
    main_menu = ["Asosiy menyu 🏠", "Главное меню 🏠"]
    change_lang = [
        "\U0001F1FA\U0001F1FF Tilni o'zgartirish \U0001F1F7\U0001F1FA",
        "\U0001F1FA\U0001F1FF Сменить язык \U0001F1F7\U0001F1FA",
    ]
    select_lang = [""" Tilni tanlang """, """Выберите язык бота """]
    type_name = ["""Ismingizni kiriting """, """Введите ваше имя """]
    send_number = [
        """Telefon raqamingizni yuboring """,
        """Оставьте свой номер телефона """,
    ]
    leave_number = ["Telefon raqamni yuborish", "Оставить номер телефона"]
    back = ["""🔙 Ortga""", """🔙 Назад"""]
    next_step = ["""Davom etish ➡️""", """Далее ➡️"""]
    seller = ["""Sotuvchi 🛍""", """Продавцам 🛍"""]
    buyer = ["""Xaridor 💵""", """Покупателям 💵"""]
    settings = ["""Sozlamalar ⚙️""", """Настройки ⚙️"""]
    language_change = ["""Tilni o\'zgartirish 🇺🇿🇷🇺""", """Смена языка 🇺🇿🇷🇺"""]
    change_phone_number = [
        """Telefon raqamni o\'zgartirish 📞""",
        """Смена номера телефона 📞""",
    ]
    change_name = ["""Ismni o\'zgartirish 👤""", """Смени имени 👤"""]
    settings_desc = ["""Sozlamalar ⚙️""", """Настройки ⚙️"""]
    your_phone_number = [
        """📌 Sizning telefon raqamingiz: [] 📌""",
        """📌 Ваш номер телефона: [] 📌""",
    ]
    send_new_phone_number = [
        """Yangi telefon raqamingizni yuboring!\n<i>Jarayonni bekor qilish uchun "🔙 Ortga" tugmasini bosing.</i>""",
        """Отправьте свой новый номер телефона!\n<i>Нажмите кнопку "🔙 Назад", чтобы отменить процесс.</i>""",
    ]
    number_is_logged = [
        "Bunday raqam bilan ro'yxatdan o'tilgan, boshqa telefon raqam kiriting",
        "Этот номер уже зарегистрирован. Введите другой номер",
    ]
    changed_your_phone_number = [
        """Sizning telefon raqamingiz muvaffaqiyatli o\'zgartirildi! ♻️""",
        """Ваш номер телефона успешно изменен! ♻️""",
    ]
    your_name = ["""Sizning ismingiz: """, """Ваше имя: """]
    send_new_name = [
        """Ismingizni o'zgartirish uchun, yangi ism kiriting:\n<i>Jarayonni bekor qilish uchun "🔙 Ortga" tugmasini bosing.</i>""",
        """Чтобы изменить свое имя, введите новое:\n<i>Нажмите кнопку "🔙 Назад", чтобы отменить процесс.</i>""",
    ]
    changed_your_name = [
        """Sizning ismingiz muvaffaqiyatli o'zgartirildi!""",
        """Ваше имя успешно изменено!""",
    ]

    successfully_registered = [
        "Siz muvaffaqiyatli ro'yxatdan o'tdingiz! ✅",
        "Вы успешно зарегистрированы! ✅",
    ]

    you_are_not_registered = [
        "Siz bizning mijozlar ro'yxatimizda yo'qsiz. Iltimos, administrator bilan bog'laning.",
        "Вы не в нашем списке клиентов. Пожалуйста, свяжитесь с администратором.",
    ]

    reconciliation_act = [
        "📑 Akt sverka",
        "📑 Акт сверки"
    ]

    fetching_reconciliation_act = [
        "Akt sverka olinmoqda...",
        "Формируется акт сверки..."
    ]

    reconciliation_act_period = [
        "Akt sverka: {start_date} - {end_date}",
        "Акт сверки: {start_date} - {end_date}"
    ]

    incorrect_date_format = [
        "Kiritilgan sana noto'g'ri formatda. Iltimos, sanani quyidagi formatda kiriting: DD.MM.YYYY",
        "Введенная дата имеет неверный формат. Пожалуйста, введите дату в следующем формате: ДД.ММ.ГГГГ",
    ]

    enter_start_date = [
        "Akt sverka uchun boshlang'ich sanani kiriting (DD.MM.YYYY)",
        "Введите начальную дату для акта сверки (ДД.ММ.ГГГГ)",
    
    ]

    enter_end_date = [
        "Akt sverka uchun tugash sanasini kiriting (DD.MM.YYYY)",
        "Введите конечную дату для акта сверки (ДД.ММ.ГГГГ)",
    ]

    order_info = [
"""
Buyurtma sanasi: <code>{deal_datetime}</code>
Menejer: <code>{manager}</code>
Miqdor: <code>{total_amount} so'm</code>
STIR: <code>{tin}</code>
"""
,
"""
Дата заказа: <code>{deal_datetime}</code>
Менеджер: <code>{manager}</code>
Сумма: <code>{total_amount} сум</code>
ИНН: <code>{tin}</code>
"""
    ]

    order_history_info = [
"""
🔸 Yetkazib berish sanasi: <code>{delivery_date}</code>
🔸 Miqdor: <code>{total_amount} so'm</code>
"""
,
"""
🔸 Дата доставки: <code>{delivery_date}</code>
🔸 Сумма: <code>{total_amount} сум</code>
"""
    ]

    new_order = [
        "🆕 <b>YANGI SAVDO!</b>",
        "🆕 <b>НОВАЯ ПРОДАЖА!</b>"
    ]

    order_status_changed_to = [
        "<b>🔄 BUYURTMA HOLATI O'ZGARDI: </b>",
        "<b>🔄 СТАТУС ЗАКАЗА ИЗМЕНИЛСЯ НА: </b>"
    ]

    order_price_changed = [
        "<b>🔄 BUYURTMA NARXI O'ZGARDI!</b>",
        "<b>🔄 СУММА ИЗМЕНИЛАСЬ!</b>"
    ]

    factura_new = [
"""📄 <b>Yangi factura qabul qilindi!</b>
<b>№:</b> <code>{doc_no}</code>
<b>Sana:</b> <code>{doc_date}</code>
"""
,
"""📄 <b>Получена новая фактура!</b>
<b>№:</b> <code>{doc_no}</code>
<b>Дата:</b> <code>{doc_date}</code>
"""
    ]

    facturas = [
        "\U0001F4C4 Fakturalar",
        "\U0001F4C4 Счет-фактуры"
    ]

    facturas_loading = [
        "Fakturalar yuklanmoqda...",
        "Счет-фактуры загружаются..."
    ]

    no_facturas_found = [
        "Qabul qilinmagan fakturalar topilmadi.",
        "Непринятых счет-фактур не найдено."
    ]

    facturas_found = [
        "Sizda {count} ta qabul qilinmagan faktura bor.",
        "У вас {count} непринятых счет-фактур."
    ]

    factura_document = [
"""\U0001F4C4 <b>Faktura</b>
<b>№:</b> <code>{doc_no}</code>
<b>Sana:</b> <code>{doc_date}</code>"""
,
"""\U0001F4C4 <b>Счет-фактура</b>
<b>№:</b> <code>{doc_no}</code>
<b>Дата:</b> <code>{doc_date}</code>"""
    ]

    factura_download_failed = [
        "Ushbu fakturani yuklab bo'lmadi: {doc_no}",
        "Не удалось загрузить счет-фактуру: {doc_no}"
    ]

    facturas_error = [
        "Fakturalarni olishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
        "Произошла ошибка при получении счет-фактур. Пожалуйста, попробуйте позже."
    ]

    factura_reminder = [
"""⚠️ <b>Elektron faktura {days} kun davomida qabul qilinmagan.</b>
<b>№:</b> <code>{doc_no}</code>
<b>Sana:</b> <code>{doc_date}</code>"""
,
"""⚠️ <b>Электронная счет-фактура не принята уже {days} дней.</b>
<b>№:</b> <code>{doc_no}</code>
<b>Дата:</b> <code>{doc_date}</code>"""
    ]

    send_phone_number = [
        "🧐 Ushbu telefon raqam orqali hech qanday ma'lumot topilmadi. Ro'yxatdan o'tgan telefon raqamni yozib qoldiring" \
            "\n\n<i>991234567 formatida</i>",
        "🧐 По этому номеру телефона не найдено никакой информации. Пожалуйста, оставьте зарегистрированный номер телефона" \
            "\n\n<i>в формате 991234567</i>",
    ]

    please_select_your_branch = [
        "Iltimos, tashkilotingizni tanlang:",
        "Пожалуйста, выберите вашу организацию:"
    ]

    please_send_your_contact_via_button = [
        "Iltimos, pastdagi tugma orqali kontaktni yuboring 👇",
        "Пожалуйста, отправьте контакт с помощью кнопки ниже 👇"
    ]

    switch_cabinet = [
        "🔄 Tashkilotni o'zgartirish",
        "🔄 Изменить организацию"
    ]

    select_cabinet = [
        "Iltimos, tashkilotni tanlang:",
        "Пожалуйста, выберите вашу организацию:"
    ]

    cabinet_switched = [
        "Siz muvaffaqiyatli ravishda {client_name} tashkilotiga o'tdingiz! ✅",
        "Вы успешно переключились на организацию {client_name}! ✅"
    ]

    sign_out = [
        "🚪 Chiqish",
        "🚪 Выйти"
    ]

    signed_out = [
        "Siz kabinetdan chiqdingiz. Qayta kirish uchun /start bosing.",
        "Вы вышли из кабинета. Для повторного входа нажмите /start."
    ]

    order_history = [
        "📦 Buyurtmalar tarixi",
        "📦 История заказов"
        ""
    ]

    client_debts = [
        "💰 Qarzdorlik",
        "💰 Задолженность"
    ]

    order_no = [
        "<b>Buyurtma №</b>",
        "<b>Заказ №</b>"
    ]

    status = [
        "Status",
        "Статус"
    ]

    active_orders = [
        "<b>Faol buyurtmalar 👇</b>",
        "<b>Активные заказы 👇</b>"
    ]

    completed_orders = [
        "<b>Yakunlangan buyurtmalar 👇</b>",
        "<b>Выполненные заказы 👇</b>"
    ]

    you_can_continue_or_return = [
        "▶️⏸️ Siz ko'proq buyurtmalarni yuklashingiz yoki asosiy menyuga qaytishingiz mumkin",
        "▶️⏸️ Вы можете загрузить больше заказов или вернуться в главное меню."
    ]

    load_more_orders = [
        "⏭️ Ko'proq buyurtmalarni yuklash",
        "⏭️ Загрузить больше заказов"
    ]

    show_completed_orders = [
        "📦 Yakunlangan buyurtmalarni ko'rsatish",
        "📦 Показать выполненные заказы"
    ]

    no_orders_found = [
        "Buyurtmalar topilmadi.",
        "Заказов не найдено."
    ]

    no_debts_found = [
        "Qarzdorlik topilmadi.",
        "Задолженность не найдена."
    ]

    total_debt_amount = [
        "<b>Jami qarzdorlik:</b> <code>{amount}</code>",
        "<b>Общая сумма задолженности:</b> <code>{amount}</code>"
    ]

    total_debt_rows = [
        "<b>Qarzdorliklar soni:</b> <code>{count}</code>",
        "<b>Количество задолженностей:</b> <code>{count}</code>"
    ]

    debts_loading = [
        "Qarzdorliklar yuklanmoqda...",
        "Задолженности загружаются..."
    ]

    payment_received = [
"""\U0001F4B0 <b>To'lovingiz qabul qilindi!</b>
<b>Summa:</b> <code>{amount}</code>
<b>Sana:</b> <code>{datetime}</code>
<b>To'lov maqsadi:</b> <code>{purpose}</code>"""
,
"""\U0001F4B0 <b>Ваш платёж получен!</b>
<b>Сумма:</b> <code>{amount}</code>
<b>Дата:</b> <code>{datetime}</code>
<b>Назначение платежа:</b> <code>{purpose}</code>"""
    ]

    feedback = [
        "\U0001F4DD Murojaat yuborish",
        "\U0001F4DD Оставить обращение"
    ]

    feedback_sent = [
"""\u2705 <b>Murojaatingiz yuborildi!</b>
<b>TTN raqami:</b> <code>{ttn_number}</code>

Tez orada javob beramiz."""
,
"""\u2705 <b>Ваше обращение отправлено!</b>
<b>Номер ТТН:</b> <code>{ttn_number}</code>

Мы ответим вам в ближайшее время."""
    ]

    feedback_answer = [
"""\U0001F4AC <b>Murojaatingizga javob berildi!</b>
<b>TTN raqami:</b> <code>{ttn_number}</code>

<b>Javob:</b>
{answer}"""
,
"""\U0001F4AC <b>На ваше обращение получен ответ!</b>
<b>Номер ТТН:</b> <code>{ttn_number}</code>

<b>Ответ:</b>
{answer}"""
    ]

    feedback_error = [
        "Murojaatni yuborishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
        "Произошла ошибка при отправке обращения. Пожалуйста, попробуйте позже."
    ]

    _ = [
        "",
        ""
    ]

    _ = [
        "",
        ""
    ]

    _ = [
        "",
        ""
    ]
