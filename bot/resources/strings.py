

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
Buyurtma raqami: <code>{deal_id}</code>
TTN raqami: <code>{delivery_number}</code>
Jo'natish sanasi: <code>{delivery_date}</code>
Savdo menejeri: <code>{sales_manager_name}</code>
Miqdor: <code>{total_amount} so'm</code>
"""
,
"""
Номер заказа: <code>{deal_id}</code>
Номер ТТН: <code>{delivery_number}</code>
Дата отгрузки: <code>{delivery_date}</code>
Менеджер по продажам: <code>{sales_manager_name}</code>
Сумма: <code>{total_amount} сум</code>
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

    # One header per status, naming what actually happened rather than the raw
    # status label. Keyed by status code in `_STATUS_HEADERS` (string_service).
    order_status_waiting = [
        "✅ <b>BUYURTMA MOLIYA BO'LIMI TOMONIDAN TASDIQLANDI</b>",
        "✅ <b>ЗАКАЗ ПОДТВЕРЖДЁН ФИНАНСОВЫМ ОТДЕЛОМ</b>"
    ]

    order_status_shipped = [
        "📦 <b>OMBOR YUKNI YIG'ISHNI BOSHLADI</b>",
        "📦 <b>СКЛАД НАЧАЛ СБОРКУ ТОВАРА</b>"
    ]

    order_status_delivered = [
        "✔️ <b>OMBOR YUKNI TAYYORLADI</b>",
        "✔️ <b>СКЛАД ПОДГОТОВИЛ ТОВАР</b>"
    ]

    order_status_archived = [
        "✅ <b>BUYURTMANGIZ YAKUNLANDI!</b>\nHisob-faktura quyida biriktirilgan \U0001F447",
        "✅ <b>ВАШ ЗАКАЗ ЗАВЕРШЁН!</b>\nСчёт-фактура прикреплена ниже \U0001F447"
    ]

    order_price_changed = [
        "<b>🔄 BUYURTMA NARXI O'ZGARDI!</b>",
        "<b>🔄 СУММА ИЗМЕНИЛАСЬ!</b>"
    ]

    order_delivery_date_changed = [
        "<b>🔄 JO'NATISH SANASI O'ZGARDI: </b><i>{old_date}</i> ➡️ <i>{new_date}</i>",
        "<b>🔄 ДАТА ОТГРУЗКИ ИЗМЕНИЛАСЬ: </b><i>{old_date}</i> ➡️ <i>{new_date}</i>"
    ]

    order_transport_on_the_way = [
"""🚚 <b>Yuk mashinaga ortildi va yo'lda!</b>
<b>Buyurtma:</b> <code>{order_no}</code>
<b>TTN raqami:</b> <code>{delivery_number}</code>
<b>Avtomobil:</b> <code>{car_name}</code>
<b>Davlat raqami:</b> <code>{car_autonum}</code>
<b>Haydovchi:</b> <code>{driver_name}</code>
<b>Telefon raqami:</b> <code>{phone_number}</code>
<b>Korobkalar soni:</b> <code>{box_count}</code>
<b>Narxi:</b> <code>{price}</code>
"""
,
"""🚚 <b>Груз погружен в машину и в пути!</b>
<b>Заказ:</b> <code>{order_no}</code>
<b>Номер ТТН:</b> <code>{delivery_number}</code>
<b>Автомобиль:</b> <code>{car_name}</code>
<b>Гос. номер:</b> <code>{car_autonum}</code>
<b>Водитель:</b> <code>{driver_name}</code>
<b>Номер телефона:</b> <code>{phone_number}</code>
<b>Количество коробок:</b> <code>{box_count}</code>
<b>Цена:</b> <code>{price}</code>
"""
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

    # price lists — the menu button, the type picker and the delivered file
    price_list = [
        "\U0001F4B2 Narxlar ro'yxati",
        "\U0001F4B2 Прайс-лист"
    ]

    price_list_type_prompt = [
"""\U0001F4B2 <b>Narxlar ro'yxati turini tanlang.</b>

Qaysi to'lov sharti bo'yicha narxlar kerak?""",
"""\U0001F4B2 <b>Выберите тип прайс-листа.</b>

Цены по какому условию оплаты вам нужны?"""
    ]

    price_list_type_negotiated = [
        "🤝 25% to'lov",
        "🤝 При 25% оплате"
    ]

    price_list_type_prepayment_100 = [
        "💯 100% to'lov",
        "💯 При 100% оплате"
    ]

    price_list_loading = [
        "Narxlar ro'yxati yuklanmoqda...",
        "Прайс-лист загружается..."
    ]

    price_list_document = [
"""\U0001F4B2 <b>{price_type}</b>

Tovarlar soni: <b>{count}</b>
Ma'lumot holati: <b>{generated_at}</b>""",
"""\U0001F4B2 <b>{price_type}</b>

Количество товаров: <b>{count}</b>
Актуально на: <b>{generated_at}</b>"""
    ]

    price_list_not_ready = [
        "Narxlar ro'yxati hozircha tayyor emas. Iltimos, birozdan so'ng urinib ko'ring.",
        "Прайс-лист пока не готов. Пожалуйста, попробуйте через несколько минут."
    ]

    price_list_error = [
        "Narxlar ro'yxatini yuborishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
        "Не удалось отправить прайс-лист. Пожалуйста, попробуйте позже."
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
<b>Sana:</b> <code>{doc_date}</code>
<b>Yuborilgan:</b> <code>{days_ago}</code>"""
,
"""\U0001F4C4 <b>Счет-фактура</b>
<b>№:</b> <code>{doc_no}</code>
<b>Дата:</b> <code>{doc_date}</code>
<b>Отправлена:</b> <code>{days_ago}</code>"""
    ]

    # "sent N days ago", with the Russian plural agreeing with the number
    factura_days_ago = [
        "{days} kun oldin",
        "{days} {plural} назад"
    ]

    factura_days_ago_today = [
        "bugun",
        "сегодня"
    ]

    factura_days_ago_unknown = [
        "noma'lum",
        "неизвестно"
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
"""⚠️ <b>Электронная счет-фактура не принята уже {days} {plural}.</b>
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

    deferment_days_info = [
        "<b>Kechiktirilgan to'lov muddati:</b> <code>{days} kun</code>",
        "<b>Отсрочка платежа:</b> <code>{days} дн.</code>"
    ]

    payment_debts_alert_header = [
        "\u26A0\uFE0F <b>Muddati o'tgan qarzdorliklar</b>",
        "\u26A0\uFE0F <b>Просроченные задолженности</b>"
    ]

    debts_loading = [
        "Qarzdorliklar yuklanmoqda...",
        "Задолженности загружаются..."
    ]

    payment_overdue = [
"""\u26A0\uFE0F <b>To'lov muddati {days} kunga o'tib ketdi!</b>
<b>Qarzdorlik summasi:</b> <code>{debt_amount} so'm</code>
<b>To'lov muddati:</b> <code>{expiry_date}</code>
"""
,
"""\u26A0\uFE0F <b>Платёж просрочен на {days} {plural}!</b>
<b>Сумма задолженности:</b> <code>{debt_amount} сум</code>
<b>Срок оплаты:</b> <code>{expiry_date}</code>
"""
    ]

    payment_due_soon = [
"""\u23F3 <b>To'lov muddati 2 kundan keyin tugaydi.</b>
<b>Qarzdorlik summasi:</b> <code>{debt_amount} so'm</code>
<b>To'lov muddati:</b> <code>{expiry_date}</code>
"""
,
"""\u23F3 <b>Срок оплаты истекает через 2 дня.</b>
<b>Сумма задолженности:</b> <code>{debt_amount} сум</code>
<b>Срок оплаты:</b> <code>{expiry_date}</code>
"""
    ]

    payment_debt_order_info = [
"""
Buyurtma raqami: <code>{deal_id}</code>
TTN raqami: <code>{delivery_number}</code>
"""
,
"""
Номер заказа: <code>{deal_id}</code>
Номер ТТН: <code>{delivery_number}</code>
"""
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
{number_line}
Tez orada javob beramiz."""
,
"""\u2705 <b>Ваше обращение отправлено!</b>
{number_line}
Мы ответим вам в ближайшее время."""
    ]

    feedback_answer = [
"""\U0001F4AC <b>Murojaatingizga javob berildi!</b>
{number_line}
<b>Javob:</b>
{answer}"""
,
"""\U0001F4AC <b>На ваше обращение получен ответ!</b>
{number_line}
<b>Ответ:</b>
{answer}"""
    ]

    # the "<label>: <number>" line above; blank for an "other" feedback, which
    # carries no reference number at all
    feedback_number_line = [
        "<b>{label}:</b> <code>{number}</code>\n",
        "<b>{label}:</b> <code>{number}</code>\n"
    ]

    # feedback types — the first thing the client picks
    feedback_type_prompt = [
"""\U0001F4DD <b>Murojaat turini tanlang.</b>

Murojaatingiz qaysi bo'limga tegishli?""",
"""\U0001F4DD <b>Выберите тип обращения.</b>

К какому отделу относится ваше обращение?"""
    ]

    feedback_type_warehouse = [
        "\U0001F69A Ombor (TTN bo'yicha)",
        "\U0001F69A Склад (по ТТН)"
    ]

    feedback_type_accounting = [
        "\U0001F4B0 Buxgalteriya (hisob-faktura bo'yicha)",
        "\U0001F4B0 Бухгалтерия (по счёту-фактуре)"
    ]

    feedback_type_other = [
        "\U0001F4AC Boshqa",
        "\U0001F4AC Другое"
    ]

    # labels for the reference number, per type
    feedback_number_label_ttn = [
        "TTN raqami",
        "Номер ТТН"
    ]

    feedback_number_label_factura = [
        "Hisob-faktura raqami",
        "Номер счёта-фактуры"
    ]

    feedback_error = [
        "Murojaatni yuborishda xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.",
        "Произошла ошибка при отправке обращения. Пожалуйста, попробуйте позже."
    ]

    feedback_ask_ttn = [
"""\U0001F4C4 <b>Yuk xati raqamini (TTN) tanlang.</b>

Quyidagi tugmani bosing va ro'yxatdan buyurtmangizni tanlang yoki TTN raqamini qo'lda kiriting.""",
"""\U0001F4C4 <b>Выберите номер товарно-транспортной накладной (ТТН).</b>

Нажмите кнопку ниже и выберите заказ из списка или введите номер ТТН вручную."""
    ]

    feedback_ask_factura = [
"""\U0001F4C4 <b>Hisob-faktura raqamini tanlang.</b>

Quyidagi tugmani bosing va ro'yxatdan hisob-fakturangizni tanlang yoki uning raqamini qo'lda kiriting.""",
"""\U0001F4C4 <b>Выберите номер счёта-фактуры.</b>

Нажмите кнопку ниже и выберите счёт-фактуру из списка или введите её номер вручную."""
    ]

    feedback_search_ttn = [
        "\U0001F50D TTN raqamini qidirish",
        "\U0001F50D Найти номер ТТН"
    ]

    feedback_search_factura = [
        "\U0001F50D Hisob-faktura raqamini qidirish",
        "\U0001F50D Найти номер счёта-фактуры"
    ]

    feedback_ttn_not_found = [
        "Bunday TTN raqamiga ega buyurtma topilmadi. Iltimos, qaytadan urinib ko'ring.",
        "Заказ с таким номером ТТН не найден. Пожалуйста, попробуйте ещё раз."
    ]

    feedback_factura_not_found = [
        "Bunday hisob-faktura raqamiga ega buyurtma topilmadi. Iltimos, qaytadan urinib ko'ring.",
        "Заказ с таким номером счёта-фактуры не найден. Пожалуйста, попробуйте ещё раз."
    ]

    feedback_ask_text = [
"""\u270D\uFE0F <b>{label}:</b> <code>{number}</code>

Endi murojaatingiz matnini yozing.""",
"""\u270D\uFE0F <b>{label}:</b> <code>{number}</code>

Теперь напишите текст вашего обращения."""
    ]

    feedback_ask_text_other = [
        "\u270D\uFE0F Murojaatingiz matnini yozing.",
        "\u270D\uFE0F Напишите текст вашего обращения."
    ]

    feedback_ask_file = [
"""\U0001F4CE Agar mavjud bo'lsa, fayl yoki rasm yuboring.

Fayl bo'lmasa, "{skip}" tugmasini bosing.""",
"""\U0001F4CE Если есть, отправьте файл или фото.

Если файла нет, нажмите кнопку "{skip}"."""
    ]

    feedback_skip_file = [
        "Fayilsiz yuborish \u27A1\uFE0F",
        "Отправить без файла \u27A1\uFE0F"
    ]

    feedback_wrong_file = [
        "Iltimos, fayl, rasm yoki video yuboring.",
        "Пожалуйста, отправьте файл, фото или видео."
    ]

    feedback_inline_order = [
        "\U0001F4E6 TTN: {ttn_number}",
        "\U0001F4E6 ТТН: {ttn_number}"
    ]

    feedback_inline_order_description = [
        "Summa: {total_amount} | Jo'natish: {delivery_date}",
        "Сумма: {total_amount} | Дата отгрузки: {delivery_date}"
    ]

    # the accounting search is keyed on the factura number end to end, so it
    # leads the result and the ТТН drops to the description as a hint
    feedback_inline_factura = [
        "\U0001F4C4 Hisob-faktura: {deal_id}",
        "\U0001F4C4 Счёт-фактура: {deal_id}"
    ]

    feedback_inline_factura_description = [
        "TTN: {ttn_number} | Summa: {total_amount}",
        "ТТН: {ttn_number} | Сумма: {total_amount}"
    ]

    feedback_inline_no_orders = [
        "Buyurtmalar topilmadi",
        "Заказы не найдены"
    ]

    feedback_inline_no_orders_description = [
        "Sizda arxivlangan buyurtmalar mavjud emas",
        "У вас нет архивных заказов"
    ]

    feedback_inline_no_facturas = [
        "Hisob-fakturalar topilmadi",
        "Счета-фактуры не найдены"
    ]

    feedback_inline_no_facturas_description = [
        "Sizda hisob-fakturalar mavjud emas",
        "У вас нет счетов-фактур"
    ]

    main_menu_with_client = [
        "\U0001F3E2 <b>{client_name}</b>\n\nAsosiy menyu \U0001F3E0",
        "\U0001F3E2 <b>{client_name}</b>\n\n\u0413\u043b\u0430\u0432\u043d\u043e\u0435 \u043c\u0435\u043d\u044e \U0001F3E0"
    ]

    staff = [
        "\U0001F465 Xodimlar",
        "\U0001F465 \u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0438"
    ]

    staff_list_title = [
        "\U0001F465 <b>{client_name}</b> xodimlari:",
        "\U0001F465 \u0421\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0438 <b>{client_name}</b>:"
    ]

    staff_list_empty = [
        "\U0001F465 <b>{client_name}</b> uchun hali xodim qo'shilmagan.\n\n"
        "Xodim qo'shsangiz, u ushbu tashkilotni botda ko'ra oladi va bildirishnomalarni oladi.",
        "\U0001F465 \u0414\u043b\u044f <b>{client_name}</b> \u0435\u0449\u0451 \u043d\u0435\u0442 \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u043e\u0432.\n\n"
        "\u0414\u043e\u0431\u0430\u0432\u043b\u0435\u043d\u043d\u044b\u0439 \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a \u0443\u0432\u0438\u0434\u0438\u0442 \u044d\u0442\u0443 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u044e \u0432 \u0431\u043e\u0442\u0435 \u0438 \u0431\u0443\u0434\u0435\u0442 \u043f\u043e\u043b\u0443\u0447\u0430\u0442\u044c \u0443\u0432\u0435\u0434\u043e\u043c\u043b\u0435\u043d\u0438\u044f."
    ]

    staff_add = [
        "\u2795 Xodim qo'shish",
        "\u2795 \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0430"
    ]

    staff_ask_phone = [
        "Xodimning telefon raqamini yuboring yoki kontaktini ulashing.\n\n"
        "<i>Masalan: 901234567</i>",
        "\u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u043d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430 \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u0430 \u0438\u043b\u0438 \u043f\u043e\u0434\u0435\u043b\u0438\u0442\u0435\u0441\u044c \u0435\u0433\u043e \u043a\u043e\u043d\u0442\u0430\u043a\u0442\u043e\u043c.\n\n"
        "<i>\u041d\u0430\u043f\u0440\u0438\u043c\u0435\u0440: 901234567</i>"
    ]

    staff_phone_invalid = [
        "\u26a0\ufe0f Telefon raqam noto'g'ri. Iltimos, qaytadan yuboring.\n\n<i>Masalan: 901234567</i>",
        "\u26a0\ufe0f \u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u043d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430. \u041f\u043e\u0436\u0430\u043b\u0443\u0439\u0441\u0442\u0430, \u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0435\u0449\u0451 \u0440\u0430\u0437.\n\n<i>\u041d\u0430\u043f\u0440\u0438\u043c\u0435\u0440: 901234567</i>"
    ]

    staff_already_added = [
        "\u2139\ufe0f {phone} allaqachon qo'shilgan.",
        "\u2139\ufe0f {phone} \u0443\u0436\u0435 \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d."
    ]

    staff_is_owner = [
        "\u2139\ufe0f {phone} ushbu tashkilot egasi, uni xodim sifatida qo'shish shart emas.",
        "\u2139\ufe0f {phone} \u2014 \u0432\u043b\u0430\u0434\u0435\u043b\u0435\u0446 \u044d\u0442\u043e\u0439 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438, \u0434\u043e\u0431\u0430\u0432\u043b\u044f\u0442\u044c \u0435\u0433\u043e \u043d\u0435 \u043d\u0443\u0436\u043d\u043e."
    ]

    staff_added = [
        "\u2705 {phone} <b>{client_name}</b> xodimi sifatida qo'shildi.",
        "\u2705 {phone} \u0434\u043e\u0431\u0430\u0432\u043b\u0435\u043d \u043a\u0430\u043a \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a <b>{client_name}</b>."
    ]

    staff_removed = [
        "\u2705 {phone} xodimlar ro'yxatidan o'chirildi.",
        "\u2705 {phone} \u0443\u0434\u0430\u043b\u0451\u043d \u0438\u0437 \u0441\u043f\u0438\u0441\u043a\u0430 \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u043e\u0432."
    ]

    staff_not_owner = [
        "\u26a0\ufe0f Faqat tashkilot egasi xodim qo'sha oladi.",
        "\u26a0\ufe0f \u0414\u043e\u0431\u0430\u0432\u043b\u044f\u0442\u044c \u0441\u043e\u0442\u0440\u0443\u0434\u043d\u0438\u043a\u043e\u0432 \u043c\u043e\u0436\u0435\u0442 \u0442\u043e\u043b\u044c\u043a\u043e \u0432\u043b\u0430\u0434\u0435\u043b\u0435\u0446 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0438."
    ]

    staff_access_granted = [
        "\U0001F511 Sizga <b>{client_name}</b> tashkiloti kabineti ochildi.\n\n"
        "Ko'rish uchun /start bosing.",
        "\U0001F511 \u0412\u0430\u043c \u043e\u0442\u043a\u0440\u044b\u0442 \u0434\u043e\u0441\u0442\u0443\u043f \u043a \u043a\u0430\u0431\u0438\u043d\u0435\u0442\u0443 <b>{client_name}</b>.\n\n"
        "\u041d\u0430\u0436\u043c\u0438\u0442\u0435 /start, \u0447\u0442\u043e\u0431\u044b \u043e\u0442\u043a\u0440\u044b\u0442\u044c."
    ]

    staff_access_revoked = [
        "\U0001F512 <b>{client_name}</b> tashkiloti kabinetiga kirish huquqingiz bekor qilindi.",
        "\U0001F512 \u0412\u0430\u0448 \u0434\u043e\u0441\u0442\u0443\u043f \u043a \u043a\u0430\u0431\u0438\u043d\u0435\u0442\u0443 <b>{client_name}</b> \u043e\u0442\u043e\u0437\u0432\u0430\u043d."
    ]

    no_accessible_clients = [
        "\U0001F9D0 Bu telefon raqam bo'yicha tashkilot topilmadi.",
        "\U0001F9D0 \u041f\u043e \u044d\u0442\u043e\u043c\u0443 \u043d\u043e\u043c\u0435\u0440\u0443 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430 \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0439 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e."
    ]

    # --- admin: bulk phone update from an xlsx file ---

    admin_only = [
        "\u26d4\ufe0f Bu buyruq faqat administratorlar uchun.",
        "\u26d4\ufe0f \u042d\u0442\u0430 \u043a\u043e\u043c\u0430\u043d\u0434\u0430 \u0434\u043e\u0441\u0442\u0443\u043f\u043d\u0430 \u0442\u043e\u043b\u044c\u043a\u043e \u0430\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440\u0430\u043c."
    ]

    update_phones_ask_file = [
        "\U0001F4CE Telefon raqamlarni yangilash uchun <b>.xlsx</b> faylni yuboring.\n\n"
        "Fayl formati:\n"
        "\u2022 <b>A ustuni</b> \u2014 \u0418\u041d\u041d (\u0422\u0418\u041d)\n"
        "\u2022 <b>D ustuni</b> \u2014 yangi telefon raqam\n"
        "\u2022 B va C ustunlari hisobga olinmaydi\n\n"
        "<i>Bekor qilish uchun /cancel.</i>",

        "\U0001F4CE \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0444\u0430\u0439\u043b <b>.xlsx</b> \u0434\u043b\u044f \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u044f \u043d\u043e\u043c\u0435\u0440\u043e\u0432 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u043e\u0432.\n\n"
        "\u0424\u043e\u0440\u043c\u0430\u0442 \u0444\u0430\u0439\u043b\u0430:\n"
        "\u2022 <b>\u041a\u043e\u043b\u043e\u043d\u043a\u0430 A</b> \u2014 \u0418\u041d\u041d\n"
        "\u2022 <b>\u041a\u043e\u043b\u043e\u043d\u043a\u0430 D</b> \u2014 \u043d\u043e\u0432\u044b\u0439 \u043d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430\n"
        "\u2022 \u041a\u043e\u043b\u043e\u043d\u043a\u0438 B \u0438 C \u043d\u0435 \u0443\u0447\u0438\u0442\u044b\u0432\u0430\u044e\u0442\u0441\u044f\n\n"
        "<i>\u0414\u043b\u044f \u043e\u0442\u043c\u0435\u043d\u044b \u2014 /cancel.</i>"
    ]

    update_phones_wrong_file = [
        "\u26a0\ufe0f Faqat <b>.xlsx</b> fayl qabul qilinadi. Qaytadan yuboring yoki /cancel bosing.",
        "\u26a0\ufe0f \u041f\u0440\u0438\u043d\u0438\u043c\u0430\u0435\u0442\u0441\u044f \u0442\u043e\u043b\u044c\u043a\u043e \u0444\u0430\u0439\u043b <b>.xlsx</b>. \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0435\u0449\u0451 \u0440\u0430\u0437 \u0438\u043b\u0438 \u043d\u0430\u0436\u043c\u0438\u0442\u0435 /cancel."
    ]

    update_phones_bad_format = [
        "\u26a0\ufe0f Fayl formati noto'g'ri.\n\n"
        "<b>A ustunida</b> \u0418\u041d\u041d, <b>D ustunida</b> telefon raqam bo'lishi kerak. "
        "Faylni tekshirib, qaytadan yuboring yoki /cancel bosing.",

        "\u26a0\ufe0f \u041d\u0435\u0432\u0435\u0440\u043d\u044b\u0439 \u0444\u043e\u0440\u043c\u0430\u0442 \u0444\u0430\u0439\u043b\u0430.\n\n"
        "\u0412 <b>\u043a\u043e\u043b\u043e\u043d\u043a\u0435 A</b> \u0434\u043e\u043b\u0436\u0435\u043d \u0431\u044b\u0442\u044c \u0418\u041d\u041d, \u0432 <b>\u043a\u043e\u043b\u043e\u043d\u043a\u0435 D</b> \u2014 \u043d\u043e\u043c\u0435\u0440 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u0430. "
        "\u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 \u0444\u0430\u0439\u043b \u0438 \u043e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0441\u043d\u043e\u0432\u0430 \u0438\u043b\u0438 \u043d\u0430\u0436\u043c\u0438\u0442\u0435 /cancel."
    ]

    update_phones_too_large = [
        "\u26a0\ufe0f Fayl juda katta (maksimum {limit} MB).",
        "\u26a0\ufe0f \u0424\u0430\u0439\u043b \u0441\u043b\u0438\u0448\u043a\u043e\u043c \u0431\u043e\u043b\u044c\u0448\u043e\u0439 (\u043c\u0430\u043a\u0441\u0438\u043c\u0443\u043c {limit} \u041c\u0411)."
    ]

    update_phones_started = [
        "\u23f3 Fayl qabul qilindi. Yangilash fonda boshlandi \u2014 tugagach xabar beraman.",
        "\u23f3 \u0424\u0430\u0439\u043b \u043f\u0440\u0438\u043d\u044f\u0442. \u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u0437\u0430\u043f\u0443\u0449\u0435\u043d\u043e \u0432 \u0444\u043e\u043d\u043e\u0432\u043e\u043c \u0440\u0435\u0436\u0438\u043c\u0435 \u2014 \u0441\u043e\u043e\u0431\u0449\u0443, \u043a\u043e\u0433\u0434\u0430 \u0437\u0430\u0432\u0435\u0440\u0448\u0438\u0442\u0441\u044f."
    ]

    update_phones_already_running = [
        "\u23f3 Oldingi yangilash hali tugamagan. Tugashini kuting.",
        "\u23f3 \u041f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0435\u0435 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u0435\u0449\u0451 \u043d\u0435 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043e. \u0414\u043e\u0436\u0434\u0438\u0442\u0435\u0441\u044c \u0435\u0433\u043e \u043e\u043a\u043e\u043d\u0447\u0430\u043d\u0438\u044f."
    ]

    update_phones_progress_export = [
        "\U0001F4E5 SmartUp'dan tashkilotlar ro'yxati yuklanmoqda\u2026",
        "\U0001F4E5 \u0417\u0430\u0433\u0440\u0443\u0436\u0430\u0435\u0442\u0441\u044f \u0441\u043f\u0438\u0441\u043e\u043a \u043e\u0440\u0433\u0430\u043d\u0438\u0437\u0430\u0446\u0438\u0439 \u0438\u0437 SmartUp\u2026"
    ]

    update_phones_progress_import = [
        "\U0001F4E4 Yangi raqamlar SmartUp'ga yozilmoqda\u2026",
        "\U0001F4E4 \u041d\u043e\u0432\u044b\u0435 \u043d\u043e\u043c\u0435\u0440\u0430 \u0437\u0430\u043f\u0438\u0441\u044b\u0432\u0430\u044e\u0442\u0441\u044f \u0432 SmartUp\u2026"
    ]

    update_phones_done = [
        "\u2705 <b>Telefon raqamlar yangilandi</b>\n\n"
        "\u2022 Fayldagi qatorlar: <b>{total}</b>\n"
        "\u2022 Yangilandi: <b>{updated}</b>\n"
        "\u2022 O'zgarmadi (raqam bir xil): <b>{unchanged}</b>\n"
        "\u2022 \u0418\u041d\u041d topilmadi: <b>{not_found}</b>\n"
        "\u2022 O'tkazib yuborilgan qatorlar: <b>{skipped}</b>",

        "\u2705 <b>\u041d\u043e\u043c\u0435\u0440\u0430 \u0442\u0435\u043b\u0435\u0444\u043e\u043d\u043e\u0432 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u044b</b>\n\n"
        "\u2022 \u0421\u0442\u0440\u043e\u043a \u0432 \u0444\u0430\u0439\u043b\u0435: <b>{total}</b>\n"
        "\u2022 \u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u043e: <b>{updated}</b>\n"
        "\u2022 \u0411\u0435\u0437 \u0438\u0437\u043c\u0435\u043d\u0435\u043d\u0438\u0439 (\u043d\u043e\u043c\u0435\u0440 \u0441\u043e\u0432\u043f\u0430\u0434\u0430\u0435\u0442): <b>{unchanged}</b>\n"
        "\u2022 \u0418\u041d\u041d \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d: <b>{not_found}</b>\n"
        "\u2022 \u041f\u0440\u043e\u043f\u0443\u0449\u0435\u043d\u043e \u0441\u0442\u0440\u043e\u043a: <b>{skipped}</b>"
    ]

    update_phones_not_found_list = [
        "\n\n\u2139\ufe0f Topilmagan \u0418\u041d\u041d:\n<code>{tins}</code>",
        "\n\n\u2139\ufe0f \u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043d\u044b\u0435 \u0418\u041d\u041d:\n<code>{tins}</code>"
    ]

    update_phones_partial_failure = [
        "\n\n\u26a0\ufe0f {count} ta guruh xatolik bilan yakunlandi \u2014 ularning raqamlari yangilanmadi.",
        "\n\n\u26a0\ufe0f {count} \u0433\u0440\u0443\u043f\u043f(\u044b) \u0437\u0430\u0432\u0435\u0440\u0448\u0438\u043b\u0438\u0441\u044c \u0441 \u043e\u0448\u0438\u0431\u043a\u043e\u0439 \u2014 \u0438\u0445 \u043d\u043e\u043c\u0435\u0440\u0430 \u043d\u0435 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u044b."
    ]

    update_phones_failed = [
        "\u274c Yangilashda xatolik yuz berdi:\n<code>{error}</code>",
        "\u274c \u041f\u0440\u0438 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0438 \u043f\u0440\u043e\u0438\u0437\u043e\u0448\u043b\u0430 \u043e\u0448\u0438\u0431\u043a\u0430:\n<code>{error}</code>"
    ]

    update_phones_interrupted = [
        "\u26a0\ufe0f Yangilash tugallanmadi \u2014 bot qayta ishga tushdi yoki jarayon to'xtatildi.\n\n"
        "Ba'zi raqamlar yangilangan bo'lishi mumkin. Faylni qaytadan yuboring \u2014 allaqachon yangilangan raqamlar o'tkazib yuboriladi.",

        "\u26a0\ufe0f \u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u043d\u0435 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043d\u043e \u2014 \u0431\u043e\u0442 \u043f\u0435\u0440\u0435\u0437\u0430\u043f\u0443\u0441\u0442\u0438\u043b\u0441\u044f \u0438\u043b\u0438 \u043f\u0440\u043e\u0446\u0435\u0441\u0441 \u0431\u044b\u043b \u043e\u0441\u0442\u0430\u043d\u043e\u0432\u043b\u0435\u043d.\n\n"
        "\u0427\u0430\u0441\u0442\u044c \u043d\u043e\u043c\u0435\u0440\u043e\u0432 \u043c\u043e\u0433\u043b\u0430 \u043e\u0431\u043d\u043e\u0432\u0438\u0442\u044c\u0441\u044f. \u041e\u0442\u043f\u0440\u0430\u0432\u044c\u0442\u0435 \u0444\u0430\u0439\u043b \u0435\u0449\u0451 \u0440\u0430\u0437 \u2014 \u0443\u0436\u0435 \u043e\u0431\u043d\u043e\u0432\u043b\u0451\u043d\u043d\u044b\u0435 \u043d\u043e\u043c\u0435\u0440\u0430 \u0431\u0443\u0434\u0443\u0442 \u043f\u0440\u043e\u043f\u0443\u0449\u0435\u043d\u044b."
    ]

    update_phones_stale_lock = [
        "\u2139\ufe0f Oldingi yangilash tugallanmagan (bot qayta ishga tushgan bo'lishi mumkin). Yangi fayl qabul qilinmoqda.",
        "\u2139\ufe0f \u041f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0435\u0435 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u043d\u0435 \u0437\u0430\u0432\u0435\u0440\u0448\u0438\u043b\u043e\u0441\u044c (\u0432\u043e\u0437\u043c\u043e\u0436\u043d\u043e, \u0431\u043e\u0442 \u043f\u0435\u0440\u0435\u0437\u0430\u043f\u0443\u0441\u043a\u0430\u043b\u0441\u044f). \u041f\u0440\u0438\u043d\u0438\u043c\u0430\u044e \u043d\u043e\u0432\u044b\u0439 \u0444\u0430\u0439\u043b."
    ]

    update_phones_all_failed = [
        "\u274c <b>Hech bir raqam yangilanmadi</b>\n\n"
        "SmartUp barcha so'rovlarni rad etdi ({count} ta guruh).\n"
        "\u2022 Fayldagi qatorlar: <b>{total}</b>\n"
        "\u2022 \u0418\u041d\u041d topilmadi: <b>{not_found}</b>",

        "\u274c <b>\u041d\u0438 \u043e\u0434\u0438\u043d \u043d\u043e\u043c\u0435\u0440 \u043d\u0435 \u043e\u0431\u043d\u043e\u0432\u043b\u0451\u043d</b>\n\n"
        "SmartUp \u043e\u0442\u043a\u043b\u043e\u043d\u0438\u043b \u0432\u0441\u0435 \u0437\u0430\u043f\u0440\u043e\u0441\u044b ({count} \u0433\u0440\u0443\u043f\u043f).\n"
        "\u2022 \u0421\u0442\u0440\u043e\u043a \u0432 \u0444\u0430\u0439\u043b\u0435: <b>{total}</b>\n"
        "\u2022 \u0418\u041d\u041d \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d: <b>{not_found}</b>"
    ]

    update_phones_cancelled = [
        "\u274c Bekor qilindi.",
        "\u274c \u041e\u0442\u043c\u0435\u043d\u0435\u043d\u043e."
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
