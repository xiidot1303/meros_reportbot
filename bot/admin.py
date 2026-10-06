from django.contrib import admin
from bot.models import *
from django.utils.html import format_html
from django.urls import reverse

class Bot_userAdmin(admin.ModelAdmin):
    def get_list_display(self, request):
        if request.user.is_superuser:
            list_display = ['name', 'username', 'phone', 'date', 'edit_button']
        else:
            list_display = ['name', 'username', 'phone', 'date']
        return list_display
    search_fields = ['name', 'username', 'phone']
    list_filter = ['date']
    list_display_links = None

    def edit_button(self, obj):
        change_url = reverse('admin:bot_bot_user_change', args=[obj.id])
        return format_html('<a class="btn btn-primary" href="{}"><i class="fas fa-edit"></i></a>', change_url)
    edit_button.short_description = 'Действие'


class CabinetAdmin(admin.ModelAdmin):
    list_display = ['bot_user', 'client', 'is_active', 'date']
    list_filter = ['is_active', 'date']
    search_fields = ['bot_user__name', 'client__name']
    autocomplete_fields = ('bot_user', 'client')


class MesageAdmin(admin.ModelAdmin):
    list_display = ['bot_users_name', 'small_text', 'open_photo', 'open_video', 'open_file', 'date']
    list_display_links = None
    fieldsets = (
        ('', {
            'fields': ['bot_users', 'text', 'photo', 'video', 'file'],
            'description': 'Выберите пользователей, которым вы хотите отправить сообщение, или просто оставьте поле пустым, чтобы отправить всем пользователям.', 
        }),

    )
    
    def bot_users_name(self, obj):
        result = ''
        if users:=obj.bot_users.all():
            for user in users:
                result += f'{user.name} {user.phone} | '
        else:
            result = 'Все'
        return result
    bot_users_name.short_description = 'Пользователи бота'

    def small_text(self, obj):
        cut_text = obj.text[:20] + ' ...' if len(obj.text) >= 20 else obj.text
        return format_html(f'<p title={obj.text}>{cut_text}</p>')
    small_text.short_description = 'Текст'

    def open_photo(self, obj):
        if obj.photo:
            change_url = f'/files/{obj.photo}'
            return format_html('<a target="_blank" class="btn btn-success" href="{}"><i class="fas fa-eye"></i> Открыть</a>', change_url)
        return None
    open_photo.short_description = 'Фото'

    def open_video(self, obj):
        if obj.video:
            change_url = f'/files/{obj.video}'
            return format_html('<a target="_blank" class="btn btn-warning" href="{}"><i class="fas fa-eye"></i> Открыть</a>', change_url)
        return None
    open_video.short_description = 'Видео'

    def open_file(self, obj):
        if obj.file:
            change_url = f'/files/{obj.file}'
            return format_html('<a target="_blank" class="btn btn-primary" href="{}"><i class="fas fa-eye"></i> Открыть</a>', change_url)
        return None
    open_file.short_description = 'Файл'

    def get_form(self, request, obj=None, **kwargs):
        form = super(MesageAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['bot_users'].widget.attrs['style'] = 'width: 20em;'
        return form

admin.site.register(Bot_user, Bot_userAdmin)
admin.site.register(Message, MesageAdmin)
admin.site.register(Cabinet, CabinetAdmin)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'status_badge', 'feedback_type', 'ttn_number', 'client', 'bot_user',
                    'taken_by_name', 'answered_by_name', 'date', 'updated_at', 'taken_at', 'answered_at')
    list_display_links = ('id', 'status_badge')
    search_fields = ('ttn_number', 'text', 'answer', 'client__name',
                     'taken_by_name', 'answered_by_name')
    list_filter = ('status', 'feedback_type', 'date', 'taken_at', 'answered_at')
    list_select_related = ('client', 'bot_user')
    date_hierarchy = 'date'
    fieldsets = (
        ('Обращение', {'fields': (
            'client', 'bot_user', 'feedback_type', 'ttn_number', 'text', 'file_id', 'file_type')}),
        ('Статус', {'fields': (
            'status', 'taken_by_name', 'taken_by', 'answered_by_name', 'answered_by')}),
        ('Ответ', {'fields': ('answer', 'answer_file_id', 'answer_file_type')}),
        ('Даты', {'fields': ('date', 'updated_at', 'taken_at', 'answered_at')}),
        ('Telegram', {'fields': ('admin_chat_id', 'admin_message_id')}),
    )
    # status and who/when are driven by the group button and the @@@ reply;
    # editing them here would leave the group message out of step
    readonly_fields = ('status', 'taken_by', 'taken_by_name', 'taken_at',
                       'date', 'updated_at', 'answered_at', 'answered_by', 'answered_by_name',
                       'answer_file_id', 'answer_file_type', 'admin_message_id', 'admin_chat_id')

    STATUS_COLORS = {
        Feedback.NEW: '#dc3545',
        Feedback.IN_PROGRESS: '#fd7e14',
        Feedback.ANSWERED: '#28a745',
    }

    @admin.display(description='Статус', ordering='status')
    def status_badge(self, obj):
        return format_html(
            '<span style="color:#fff;background:{};padding:2px 8px;border-radius:10px;white-space:nowrap">{}</span>',
            self.STATUS_COLORS.get(obj.status, '#6c757d'), obj.get_status_display())


@admin.register(ClientStaff)
class ClientStaffAdmin(admin.ModelAdmin):
    list_display = ('phone', 'name', 'client', 'added_by', 'date')
    search_fields = ('phone', 'name', 'client__name')
    list_filter = ('date',)
    autocomplete_fields = ()
    readonly_fields = ('date',)
    autocomplete_fields = ('client',)
