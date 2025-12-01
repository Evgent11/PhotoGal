from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


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