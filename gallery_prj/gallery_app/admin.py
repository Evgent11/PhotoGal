from django.contrib import admin
from .models import Service

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type', 'price', 'duration', 'is_active', 'order')
    list_filter = ('service_type', 'is_active')
    list_editable = ('price', 'order', 'is_active')
    search_fields = ('name', 'description')
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'service_type')
        }),
        ('Детали услуги', {
            'fields': ('price', 'duration', 'order', 'is_active')
        }),
    )