from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import Service, Booking
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
import datetime


# ============ BOOKING FORM ============
class BookingAdminForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'
        widgets = {
            'user': forms.Select(attrs={'class': 'vTextField'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поле user необязательным в форме
        self.fields['user'].required = False
        self.fields['user'].empty_label = "---------"
        # Настраиваем queryset для пользователей
        self.fields['user'].queryset = User.objects.filter(is_active=True).order_by('username')


# ============ BOOKING ADMIN ============
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    form = BookingAdminForm
    list_display = ('booking_id', 'client_name', 'service', 'booking_date',
                    'booking_time', 'status_display', 'total_price', 'created_at', 'user_info')
    list_filter = ('status', 'booking_date', 'service', 'created_at')
    search_fields = ('client_name', 'client_phone', 'client_email',
                     'service__name', 'id', 'user__username', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'status_display', 'total_price_display')
    list_per_page = 25
    actions = ['confirm_bookings', 'reject_bookings', 'complete_bookings']
    date_hierarchy = 'booking_date'

    fieldsets = (
        ('Основная информация', {
            'fields': ('id', 'user', 'service', 'status', 'created_at', 'status_display')
        }),
        ('Детали съемки', {
            'fields': ('booking_date', 'booking_time', 'duration', 'location')
        }),
        ('Информация о клиенте', {
            'fields': ('client_name', 'client_phone', 'client_email', 'client_message')
        }),
        ('Финансы', {
            'fields': ('price_agreed', 'total_price_display')
        }),
        ('Административные заметки', {
            'fields': ('admin_notes', 'admin_user', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def booking_id(self, obj):
        return format_html('<strong>{}</strong>', str(obj.id)[:8])

    booking_id.short_description = 'ID'

    def user_info(self, obj):
        if obj.user:
            return format_html('{}<br><small>{}</small>', obj.user.username, obj.user.email)
        return "—"

    user_info.short_description = 'Пользователь'

    def status_display(self, obj):
        """Отображение статуса с цветовым оформлением"""
        colors = {
            'pending': '#FF9800',  # оранжевый
            'confirmed': '#4CAF50',  # зеленый
            'rejected': '#f44336',  # красный
            'completed': '#2196F3',  # синий
            'cancelled': '#9E9E9E',  # серый
        }
        color = colors.get(obj.status, '#9E9E9E')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 12px; border-radius: 15px; font-size: 12px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )

    status_display.short_description = 'Статус'
    status_display.admin_order_field = 'status'

    def total_price(self, obj):
        price = obj.get_total_price()
        return f"{price} руб." if price else "—"

    total_price.short_description = 'Стоимость'
    total_price.admin_order_field = 'price_agreed'

    def total_price_display(self, obj):
        price = obj.get_total_price()
        return f"{price} руб." if price else "Не указана"

    total_price_display.short_description = 'Общая стоимость'

    # Кастомные действия для массового изменения статуса
    def confirm_bookings(self, request, queryset):
        """Подтвердить выбранные бронирования"""
        updated = queryset.update(status='confirmed', admin_user=request.user)
        self.message_user(request, f"{updated} бронирований подтверждено.")

    confirm_bookings.short_description = "✅ Подтвердить выбранные бронирования"

    def reject_bookings(self, request, queryset):
        """Отклонить выбранные бронирования"""
        updated = queryset.update(status='rejected', admin_user=request.user)
        self.message_user(request, f"{updated} бронирований отклонено.")

    reject_bookings.short_description = "❌ Отклонить выбранные бронирования"

    def complete_bookings(self, request, queryset):
        """Пометить как выполненные"""
        updated = queryset.update(status='completed', admin_user=request.user)
        self.message_user(request, f"{updated} бронирований отмечены как выполненные.")

    complete_bookings.short_description = "✅ Пометить как выполненные"

    # Фильтрация для не-суперпользователей
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Обычные сотрудники видят только бронирования в ожидании
        return qs.filter(status='pending')

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        # Если пользователь не выбран, устанавливаем текущего пользователя как создателя бронирования
        if not obj.user:
            obj.user = request.user

        # Если изменен статус и не установлен admin_user, устанавливаем текущего пользователя
        if not obj.admin_user and 'status' in form.changed_data:
            obj.admin_user = request.user

        super().save_model(request, obj, form, change)

    def get_form(self, request, obj=None, **kwargs):
        """Переопределяем форму для отображения"""
        form = super().get_form(request, obj, **kwargs)

        # Если это создание нового объекта (не редактирование)
        if not obj:
            # Скрываем некоторые поля при создании
            form.base_fields['admin_notes'].widget.attrs['readonly'] = False
            form.base_fields['admin_user'].widget.attrs['readonly'] = True
            form.base_fields['admin_user'].widget.attrs['disabled'] = True

        return form

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/booking_admin.js',)


# ============ SERVICE ADMIN ============
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'service_type_display', 'price', 'duration',
                    'can_be_booked_badge', 'is_active_badge', 'order')
    list_filter = ('service_type', 'is_active', 'can_be_booked')
    search_fields = ('name', 'description')
    list_editable = ('price', 'order')
    list_per_page = 20

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'service_type')
        }),
        ('Цена и продолжительность', {
            'fields': ('price', 'duration')
        }),
        ('Настройки бронирования', {
            'fields': ('can_be_booked', 'min_booking_hours', 'max_booking_hours', 'preparation_time')
        }),
        ('Отображение', {
            'fields': ('is_active', 'order')
        }),
    )

    def service_type_display(self, obj):
        icons = {
            'PHOTO': '📷',
            'VIDEO': '🎥',
            'EDITING': '💻',
            'OTHER': '✨',
        }
        icon = icons.get(obj.service_type, '✨')
        return f"{icon} {obj.get_service_type_display()}"

    service_type_display.short_description = 'Тип услуги'

    def can_be_booked_badge(self, obj):
        if obj.can_be_booked:
            return format_html(
                '<span style="background-color: #4CAF50; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px;">✓ Можно бронировать</span>'
            )
        return format_html(
            '<span style="background-color: #f44336; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px;">✗ Нельзя бронировать</span>'
        )

    can_be_booked_badge.short_description = 'Бронирование'

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html(
                '<span style="background-color: #4CAF50; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px;">Активна</span>'
            )
        return format_html(
            '<span style="background-color: #9E9E9E; color: white; padding: 3px 8px; border-radius: 10px; font-size: 11px;">Неактивна</span>'
        )

    is_active_badge.short_description = 'Статус'


# ============ CUSTOM USER ADMIN ============
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_staff', 'is_active', 'date_joined', 'last_login')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_per_page = 25

    actions = ['activate_users', 'deactivate_users', 'make_staff', 'remove_staff']

    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} пользователей активировано.")

    activate_users.short_description = "✅ Активировать выбранных пользователей"

    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} пользователей деактивировано.")

    deactivate_users.short_description = "❌ Деактивировать выбранных пользователей"

    def make_staff(self, request, queryset):
        updated = queryset.update(is_staff=True)
        self.message_user(request, f"{updated} пользователей назначены сотрудниками.")

    make_staff.short_description = "👑 Назначить сотрудниками"

    def remove_staff(self, request, queryset):
        updated = queryset.update(is_staff=False)
        self.message_user(request, f"{updated} пользователей удалены из сотрудников.")

    remove_staff.short_description = "👑 Убрать из сотрудников"


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)