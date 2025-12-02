from django.db import models
from django.contrib.auth.models import User
import uuid

class Service(models.Model):
    SERVICE_TYPES = [
        ('PHOTO', 'Фотосъемка'),
        ('VIDEO', 'Видеосъемка'),
        ('EDITING', 'Обработка'),
        ('OTHER', 'Другое'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название услуги')
    description = models.TextField(verbose_name='Описание услуги')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Цена')
    duration = models.CharField(max_length=100, blank=True, verbose_name='Продолжительность')
    service_type = models.CharField(max_length=20, choices=SERVICE_TYPES, verbose_name='Тип услуги')
    is_active = models.BooleanField(default=True, verbose_name='Активная услуга')
    order = models.IntegerField(default=0, verbose_name='Порядок отображения')


    can_be_booked = models.BooleanField(default=True, verbose_name='Можно забронировать')
    min_booking_hours = models.IntegerField(default=1, verbose_name='Минимальное время бронирования (часы)')
    max_booking_hours = models.IntegerField(default=8, verbose_name='Максимальное время бронирования (часы)')
    preparation_time = models.IntegerField(default=1, verbose_name='Время на подготовку (часы)')

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['order', 'service_type', 'name']

    def __str__(self):
        return f"{self.name} - {self.price} руб."


class Booking(models.Model):
    """Модель бронирования услуги"""

    STATUS_CHOICES = [
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждено'),
        ('rejected', 'Отклонено'),
        ('completed', 'Выполнено'),
        ('cancelled', 'Отменено'),
    ]

    # Основная информация
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    service = models.ForeignKey('Service', on_delete=models.CASCADE, verbose_name='Услуга')

    # Детали бронирования
    booking_date = models.DateField(verbose_name='Дата съемки')
    booking_time = models.TimeField(verbose_name='Время съемки')
    duration = models.IntegerField(verbose_name='Продолжительность (часы)', default=2)
    location = models.CharField(max_length=500, verbose_name='Место съемки', blank=True)

    # Контактная информация
    client_name = models.CharField(max_length=200, verbose_name='Имя клиента')
    client_phone = models.CharField(max_length=20, verbose_name='Телефон')
    client_email = models.EmailField(verbose_name='Email')
    client_message = models.TextField(verbose_name='Пожелания и комментарии', blank=True)

    # Статус и управление
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='Статус')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    # Для администратора
    admin_notes = models.TextField(verbose_name='Заметки администратора', blank=True)
    price_agreed = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Согласованная цена', null=True,
                                       blank=True)
    admin_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='bookings_managed', verbose_name='Подтвердил администратор')

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'
        ordering = ['-booking_date', '-booking_time']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['booking_date']),
            models.Index(fields=['user', 'status']),
        ]

    def __str__(self):
        return f"{self.client_name} - {self.service.name} ({self.get_status_display()})"

    def get_total_price(self):

        if self.price_agreed:
            return self.price_agreed
        return self.service.price * self.duration

    def is_upcoming(self):

        from django.utils import timezone
        import datetime
        booking_datetime = datetime.datetime.combine(self.booking_date, self.booking_time)
        return booking_datetime > timezone.now()

    def get_days_until(self):
        """Возвращает количество дней до съемки"""
        from django.utils import timezone
        import datetime
        booking_datetime = datetime.datetime.combine(self.booking_date, self.booking_time)
        today = timezone.now().date()
        return (self.booking_date - today).days