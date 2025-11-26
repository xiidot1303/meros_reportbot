from django.contrib import admin
from app.models import *

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'external_id', 'tg_id')
    search_fields = ('name', 'phone', 'external_id', 'tg_id')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('deal_id', 'client', 'status', 'total_amount', 'delivery_date')
    search_fields = ('deal_id', 'client__name', 'manager')
    list_filter = ('status', 'delivery_date', 'client')