

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
Yetkazib berish sanasi: <code>{delivery_date}</code>
Menejer: <code>{manager}</code>
Miqdor: <code>{total_amount}</code> UZS
STIR: <code>{tin}</code>
"""
,
"""
Дата доставки: <code>{delivery_date}</code>
Менеджер: <code>{manager}</code>
Сумма: <code>{total_amount}</code> UZS
ИНН: <code>{tin}</code>
"""
    ]

    new_order = [
        "🆕 <b>YANGI SAVDO!</b>",
        "🆕 <b>НОВАЯ ПРОДАЖА!</b>"
    ]

    order_status_changed_to = [
        "BUYURTMA HOLATI O'ZGARDI: ",
        "СТАТУС ЗАКАЗА ИЗМЕНИЛСЯ НА: "
    ]

    send_phone_number = [
        "🧐 Ushbu telefon raqam orqali hech qanday ma'lumot topilmadi. Ro'yxatdan o'tgan telefon raqamni yozib qoldiring" \
            "\n\n<i>991234567 formatida</i>",
        "🧐 По этому номеру телефона не найдено никакой информации. Пожалуйста, оставьте зарегистрированный номер телефона" \
            "\n\n<i>в формате 991234567</i>",
    ]

    please_select_your_branch = [
        "Iltimos, fillialingizni tanlang:",
        "Пожалуйста, выберите ваш филиал:"
    ]

    please_send_your_contact_via_button = [
        "Iltimos, pastdagi tugma orqali kontaktni yuboring 👇",
        "Пожалуйста, отправьте контакт с помощью кнопки ниже 👇"
    ]

    switch_cabinet = [
        "🔄 Kabinetni almashtirish",
        "🔄 Смена кабинета"
    ]

    select_cabinet = [
        "Iltimos, kabinetni tanlang:",
        "Пожалуйста, выберите кабинет:"
    ]

    add_cabinet = [
        "➕ Yangi kabinet qo'shish",
        "➕ Добавить новый кабинет"
    ]

    cabinet_switched = [
        "Siz muvaffaqiyatli ravishda {client_name} kabinetiga o'tdingiz! ✅",
        "Вы успешно переключились на кабинет {client_name}! ✅"
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
