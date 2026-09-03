from django.db import models
from django.core.validators import FileExtensionValidator
from asgiref.sync import sync_to_async
from app.models import Client
from django.db.models import Q


class Bot_user(models.Model):
    user_id = models.BigIntegerField(null=True)
    name = models.CharField(null=True, blank=True, max_length=256, default='', verbose_name='Имя')
    username = models.CharField(null=True, blank=True, max_length=256, verbose_name='username')
    firstname = models.CharField(null=True, blank=True, max_length=256, verbose_name='Никнейм')
    phone = models.CharField(null=True, blank=True, max_length=16, default='', verbose_name='Телефон')
    LANG_CHOICES = [
        (0, 'uz'),
        (1, 'ru'),
    ]
    lang = models.IntegerField(null=True, blank=True, choices=LANG_CHOICES, default=0, verbose_name='Язык')
    date = models.DateTimeField(db_index=True, null=True, auto_now_add=True, blank=True, verbose_name='Дата регистрации')

    def __str__(self) -> str:
        try:
            return self.name + ' ' + str(self.phone)
        except:
            return super().__str__()

    class Meta:
        verbose_name = "Пользователь бота"
        verbose_name_plural = "Пользователи бота"

    @property
    async def get_active_cabinet(self):
        return await Cabinet.objects.aget(bot_user=self, is_active=True)
    

class Cabinet(models.Model):
    bot_user = models.ForeignKey('Bot_user', null=True, blank=True, on_delete=models.CASCADE, verbose_name='Пользователь бота')
    client = models.ForeignKey('app.Client', null=True, blank=True, on_delete=models.CASCADE, verbose_name='Клиент')
    date = models.DateTimeField(db_index=True, null=True, auto_now_add=True, blank=True, verbose_name='Дата входа')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = "Кабинет"
        verbose_name_plural = "Кабинеты"

    def __str__(self) -> str:
        try:
            return f"{self.client.name}"
        except:
            return super().__str__()
    
    async def get_client(self) -> Client:
        """The cabinet's client, fetched without blocking the event loop.

        A method rather than a property: the async FK fetch has to be awaited
        on a call, so every caller uses `await cabinet.get_client()`.
        """
        if self.client_id is None:
            return None
        return await Client.objects.aget(pk=self.client_id)


class Message(models.Model):
    bot_users = models.ManyToManyField('bot.Bot_user', blank=True, related_name='bot_users_list', verbose_name='Пользователи бота')
    text = models.TextField(null=True, blank=False, max_length=1024, verbose_name='Текст')
    photo = models.FileField(null=True, blank=True, upload_to="message/photo/", verbose_name='Фото',
        validators=[FileExtensionValidator(allowed_extensions=['jpg','jpeg','png','bmp','gif'])]
    )
    video = models.FileField(
        null=True, blank=True, upload_to="message/video/", verbose_name='Видео',
        validators=[FileExtensionValidator(allowed_extensions=['MOV','avi','mp4','webm','mkv'])]
        )
    file = models.FileField(null=True, blank=True, upload_to="message/file/", verbose_name='Файл')
    is_sent = models.BooleanField(default=False)
    date = models.DateTimeField(db_index=True, null=True, auto_now_add=True, blank=True, verbose_name='Дата')

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"

class Feedback(models.Model):
    # what the feedback is about — decides which reference number is asked for
    WAREHOUSE = 'warehouse'
    ACCOUNTING = 'accounting'
    OTHER = 'other'
    TYPE_CHOICES = [
        (WAREHOUSE, 'Склад'),
        (ACCOUNTING, 'Бухгалтерия'),
        (OTHER, 'Другое'),
    ]

    bot_user = models.ForeignKey('Bot_user', null=True, blank=True, on_delete=models.CASCADE, verbose_name='Пользователь бота')
    client = models.ForeignKey('app.Client', null=True, blank=True, on_delete=models.SET_NULL, verbose_name='Клиент')
    feedback_type = models.CharField(
        max_length=16, choices=TYPE_CHOICES, default=WAREHOUSE,
        db_index=True, verbose_name='Тип обращения')
    # ТТН for a warehouse issue, счёт-фактура (Order.deal_id) for an accounting
    # one, empty for "other" — the reference number the whole thread is keyed on
    ttn_number = models.CharField(max_length=64, blank=True, default='', db_index=True, verbose_name='Номер ТТН / счёта-фактуры')
    text = models.TextField(verbose_name='Текст обращения')
    file_id = models.CharField(max_length=256, null=True, blank=True, verbose_name='File ID вложения обращения')
    file_type = models.CharField(max_length=16, null=True, blank=True, verbose_name='Тип вложения обращения')
    answer = models.TextField(null=True, blank=True, verbose_name='Ответ администратора')
    answer_file_id = models.CharField(max_length=256, null=True, blank=True, verbose_name='File ID вложения ответа')
    answer_file_type = models.CharField(max_length=16, null=True, blank=True, verbose_name='Тип вложения ответа')
    answered_by = models.BigIntegerField(null=True, blank=True, verbose_name='Telegram ID администратора')
    answered_by_name = models.CharField(max_length=256, null=True, blank=True, verbose_name='Администратор')
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name='Дата ответа')
    admin_message_id = models.BigIntegerField(null=True, blank=True, verbose_name='ID сообщения в группе админов')
    date = models.DateTimeField(db_index=True, null=True, auto_now_add=True, blank=True, verbose_name='Дата обращения')

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"
        ordering = ['-date']

    def __str__(self) -> str:
        if not self.ttn_number:
            return f"{self.get_feedback_type_display()} #{self.pk}"
        return f"{self.number_label} {self.ttn_number}"

    @property
    def is_answered(self):
        return bool(self.answer or self.answer_file_id)

    @property
    def number_label(self):
        """Russian label for the reference number, by feedback type."""
        return 'Счёт-фактура' if self.feedback_type == self.ACCOUNTING else 'ТТН'


class ClientStaff(models.Model):
    """A phone number an owner has granted access to one of their clients.

    Access to a `Client` comes from two places: owning it (the bot user's phone
    equals `Client.phone`) or being listed here. Both are keyed on the phone
    number rather than on `Bot_user`, so a grant can be issued before the staff
    member has ever opened the bot.
    """
    client = models.ForeignKey(
        'app.Client', on_delete=models.CASCADE, related_name='staff',
        verbose_name='Клиент')
    phone = models.CharField(max_length=16, db_index=True, verbose_name='Телефон')
    name = models.CharField(
        null=True, blank=True, max_length=256, default='', verbose_name='Имя')
    added_by = models.ForeignKey(
        'Bot_user', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='granted_staff', verbose_name='Кем добавлен')
    date = models.DateTimeField(
        db_index=True, null=True, auto_now_add=True, blank=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = "Сотрудник клиента"
        verbose_name_plural = "Сотрудники клиентов"
        unique_together = [('client', 'phone')]

    def __str__(self) -> str:
        try:
            return f"{self.phone} — {self.client.name}"
        except:
            return super().__str__()
