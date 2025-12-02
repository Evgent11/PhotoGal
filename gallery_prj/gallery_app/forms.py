from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Booking, Service
from django.utils import timezone
import datetime

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Введите ваш email'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Добавляем классы и placeholder для всех полей
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Введите имя пользователя'
        })

        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Введите пароль'
        })

        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Подтвердите пароль'
        })

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Этот email уже используется')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('Это имя пользователя уже занято')
        return username


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Введите имя пользователя'
        })

        self.fields['password'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Введите пароль'
        })

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if '@' in username:
            try:
                user = User.objects.get(email=username)
                return user.username
            except User.DoesNotExist:
                raise ValidationError('Неверный email или пароль')
        return username

    class BookingForm(forms.ModelForm):
        """Форма для создания бронирования"""

        # Дополнительные поля для валидации
        confirm_terms = forms.BooleanField(
            required=True,
            label='Я согласен с условиями бронирования',
            widget=forms.CheckboxInput(attrs={'class': 'checkbox-input'})
        )

        class Meta:
            model = Booking
            fields = [
                'service', 'booking_date', 'booking_time',
                'duration', 'location', 'client_name',
                'client_phone', 'client_email', 'client_message'
            ]
            widgets = {
                'booking_date': forms.DateInput(
                    attrs={'type': 'date', 'class': 'form-input', 'min': timezone.now().date().isoformat()}
                ),
                'booking_time': forms.TimeInput(
                    attrs={'type': 'time', 'class': 'form-input'}
                ),
                'duration': forms.NumberInput(
                    attrs={'class': 'form-input', 'min': 1, 'max': 8, 'step': 1}
                ),
                'location': forms.TextInput(
                    attrs={'class': 'form-input', 'placeholder': 'Адрес или название места съемки'}
                ),
                'client_name': forms.TextInput(
                    attrs={'class': 'form-input', 'placeholder': 'Ваше полное имя'}
                ),
                'client_phone': forms.TextInput(
                    attrs={'class': 'form-input', 'placeholder': '+7 (999) 999-99-99'}
                ),
                'client_email': forms.EmailInput(
                    attrs={'class': 'form-input', 'placeholder': 'email@example.com'}
                ),
                'client_message': forms.Textarea(
                    attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Опишите ваши пожелания...'}
                ),
                'service': forms.Select(
                    attrs={'class': 'form-input'}
                ),
            }
            labels = {
                'booking_date': 'Дата съемки',
                'booking_time': 'Время начала',
                'duration': 'Продолжительность (часы)',
                'location': 'Место съемки',
                'client_name': 'Ваше имя',
                'client_phone': 'Контактный телефон',
                'client_email': 'Email для связи',
                'client_message': 'Дополнительные пожелания',
                'service': 'Выберите услугу',
            }

        def __init__(self, *args, **kwargs):
            self.request = kwargs.pop('request', None)
            super().__init__(*args, **kwargs)

            # Показываем только услуги, которые можно забронировать
            self.fields['service'].queryset = Service.objects.filter(
                is_active=True,
                can_be_booked=True
            ).order_by('order', 'name')

            # Устанавливаем минимальную дату - завтра
            tomorrow = timezone.now().date() + datetime.timedelta(days=1)
            self.fields['booking_date'].widget.attrs['min'] = tomorrow.isoformat()

            # Если пользователь авторизован, заполняем его данные
            if self.request and self.request.user.is_authenticated:
                user = self.request.user
                self.fields['client_name'].initial = user.get_full_name() or user.username
                self.fields['client_email'].initial = user.email

        def clean_booking_date(self):
            """Валидация даты бронирования"""
            booking_date = self.cleaned_data.get('booking_date')

            if booking_date:
                # Нельзя бронировать в прошлом
                if booking_date < timezone.now().date():
                    raise ValidationError('Нельзя выбрать прошедшую дату')

                # Нельзя бронировать на ближайшие 2 дня (минимум 48 часов на подготовку)
                min_date = timezone.now().date() + datetime.timedelta(days=2)
                if booking_date < min_date:
                    raise ValidationError('Бронирование возможно минимум за 48 часов')

                # Проверяем, не воскресенье ли
                if booking_date.weekday() == 6:  # 6 = воскресенье
                    raise ValidationError('Съемки не проводятся по воскресеньям')

            return booking_date

        def clean_duration(self):
            """Валидация продолжительности"""
            duration = self.cleaned_data.get('duration')
            service = self.cleaned_data.get('service')

            if duration and service:
                if duration < service.min_booking_hours:
                    raise ValidationError(f'Минимальная продолжительность - {service.min_booking_hours} часов')
                if duration > service.max_booking_hours:
                    raise ValidationError(f'Максимальная продолжительность - {service.max_booking_hours} часов')

            return duration

        def clean(self):
            """Общая валидация формы"""
            cleaned_data = super().clean()

            # Проверяем, что время выбрано для буднего дня
            booking_date = cleaned_data.get('booking_date')
            booking_time = cleaned_data.get('booking_time')

            if booking_date and booking_time:
                booking_datetime = datetime.datetime.combine(booking_date, booking_time)

                # Рабочее время с 9:00 до 21:00
                start_time = datetime.time(9, 0)
                end_time = datetime.time(21, 0)

                if booking_time < start_time or booking_time > end_time:
                    self.add_error('booking_time', 'Съемки проводятся с 9:00 до 21:00')

            return cleaned_data

    class AdminBookingForm(forms.ModelForm):
        """Форма для администратора для изменения статуса бронирования"""

        class Meta:
            model = Booking
            fields = ['status', 'price_agreed', 'admin_notes']
            widgets = {
                'admin_notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
                'price_agreed': forms.NumberInput(attrs={'class': 'form-input'}),
                'status': forms.Select(attrs={'class': 'form-input'}),
            }


class BookingForm(forms.ModelForm):
    """Форма для создания бронирования"""

    # Дополнительные поля для валидации
    confirm_terms = forms.BooleanField(
        required=True,
        label='Я согласен с условиями бронирования',
        widget=forms.CheckboxInput(attrs={'class': 'checkbox-input'})
    )

    class Meta:
        model = Booking
        fields = [
            'service', 'booking_date', 'booking_time',
            'duration', 'location', 'client_name',
            'client_phone', 'client_email', 'client_message'
        ]
        widgets = {
            'booking_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-input', 'min': timezone.now().date().isoformat()}
            ),
            'booking_time': forms.TimeInput(
                attrs={'type': 'time', 'class': 'form-input'}
            ),
            'duration': forms.NumberInput(
                attrs={'class': 'form-input', 'min': 1, 'max': 8, 'step': 1}
            ),
            'location': forms.TextInput(
                attrs={'class': 'form-input', 'placeholder': 'Адрес или название места съемки'}
            ),
            'client_name': forms.TextInput(
                attrs={'class': 'form-input', 'placeholder': 'Ваше полное имя'}
            ),
            'client_phone': forms.TextInput(
                attrs={'class': 'form-input', 'placeholder': '+7 (999) 999-99-99'}
            ),
            'client_email': forms.EmailInput(
                attrs={'class': 'form-input', 'placeholder': 'email@example.com'}
            ),
            'client_message': forms.Textarea(
                attrs={'class': 'form-input', 'rows': 4, 'placeholder': 'Опишите ваши пожелания...'}
            ),
            'service': forms.Select(
                attrs={'class': 'form-input'}
            ),
        }
        labels = {
            'booking_date': 'Дата съемки',
            'booking_time': 'Время начала',
            'duration': 'Продолжительность (часы)',
            'location': 'Место съемки',
            'client_name': 'Ваше имя',
            'client_phone': 'Контактный телефон',
            'client_email': 'Email для связи',
            'client_message': 'Дополнительные пожелания',
            'service': 'Выберите услугу',
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

        # Показываем только услуги, которые можно забронировать
        self.fields['service'].queryset = Service.objects.filter(
            is_active=True,
            can_be_booked=True
        ).order_by('order', 'name')


        tomorrow = timezone.now().date() + datetime.timedelta(days=1)
        self.fields['booking_date'].widget.attrs['min'] = tomorrow.isoformat()


        if self.request and self.request.user.is_authenticated:
            user = self.request.user
            self.fields['client_name'].initial = user.get_full_name() or user.username
            self.fields['client_email'].initial = user.email

    def clean_booking_date(self):
        """Валидация даты бронирования"""
        booking_date = self.cleaned_data.get('booking_date')

        if booking_date:
            # Нельзя бронировать в прошлом
            if booking_date < timezone.now().date():
                raise ValidationError('Нельзя выбрать прошедшую дату')

            # Нельзя бронировать на ближайшие 2 дня (минимум 48 часов на подготовку)
            min_date = timezone.now().date() + datetime.timedelta(days=2)
            if booking_date < min_date:
                raise ValidationError('Бронирование возможно минимум за 48 часов')

            # Проверяем, не воскресенье ли
            if booking_date.weekday() == 6:  # 6 = воскресенье
                raise ValidationError('Съемки не проводятся по воскресеньям')

        return booking_date

    def clean_duration(self):
        duration = self.cleaned_data.get('duration')
        service = self.cleaned_data.get('service')

        if duration and service:
            if duration < service.min_booking_hours:
                raise ValidationError(f'Минимальная продолжительность - {service.min_booking_hours} часов')
            if duration > service.max_booking_hours:
                raise ValidationError(f'Максимальная продолжительность - {service.max_booking_hours} часов')

        return duration

    def clean(self):
        cleaned_data = super().clean()

        # Проверяем, что время выбрано для буднего дня
        booking_date = cleaned_data.get('booking_date')
        booking_time = cleaned_data.get('booking_time')

        if booking_date and booking_time:
            booking_datetime = datetime.datetime.combine(booking_date, booking_time)

            # Рабочее время с 9:00 до 21:00
            start_time = datetime.time(9, 0)
            end_time = datetime.time(21, 0)

            if booking_time < start_time or booking_time > end_time:
                self.add_error('booking_time', 'Съемки проводятся с 9:00 до 21:00')

        return cleaned_data


class AdminBookingForm(forms.ModelForm):

    class Meta:
        model = Booking
        fields = ['status', 'price_agreed', 'admin_notes']
        widgets = {
            'admin_notes': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
            'price_agreed': forms.NumberInput(attrs={'class': 'form-input'}),
            'status': forms.Select(attrs={'class': 'form-input'}),
        }