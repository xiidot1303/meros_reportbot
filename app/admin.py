from django.contrib import admin
from app.models import *

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'external_id', 'tg_id')
    search_fields = ('name', 'external_id', 'tg_id')