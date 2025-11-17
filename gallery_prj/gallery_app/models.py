from django.db import models


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

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['order', 'service_type', 'name']

    def __str__(self):
        return f"{self.name} - {self.price} руб."
