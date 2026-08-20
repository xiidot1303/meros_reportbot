from django.contrib import admin
from app.models import *

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'external_id', 'tg_id')
    search_fields = ('name', 'phone', 'external_id', 'tg_id')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('deal_id', 'client', 'client__phone', 'status', 'total_amount', 'delivery_date')
    search_fields = ('deal_id', 'client__name', 'manager')
    list_filter = ('status', 'delivery_date', 'client')


@admin.register(Texture)
class TextureAdmin(admin.ModelAdmin):
    list_display = ('doc_id', 'doc_no', 'doc_date', 'client', 'doc_status', 'total_delivery_sum_with_vat')
    search_fields = ('doc_id', 'doc_no', 'client__name')
    list_filter = ('doc_status', 'doc_date', 'client')


@admin.register(OrderTransport)
class OrderTransportAdmin(admin.ModelAdmin):
    list_display = ('order_id_external', 'car_brand', 'car_model', 'car_autonum', 'driver_name', 'phone_number', 'created_at')
    search_fields = ('order_id_external', 'car_autonum', 'car_brand', 'car_model', 'firstname', 'lastname', 'phone_number')
    list_filter = ('created_at', 'car_brand')
    readonly_fields = ('created_at', 'updated_at')
