from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.models import User  # ИМПОРТ МОДЕЛИ USER
from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .models import Service
import time
from django.contrib.auth import logout


# Главная страница
def home_view(request):
    try:
        user_count = User.objects.count()
    except:
        user_count = 0

    context = {
        'user_count': user_count,
    }
    return render(request, 'home.html', context)


# Страница цен
def prices_view(request):
    services = Service.objects.filter(is_active=True)
    services_by_type = {}
    for service in services:
        if service.service_type not in services_by_type:
            services_by_type[service.service_type] = []
        services_by_type[service.service_type].append(service)

    return render(request, 'prices.html', {
        'services': services,
        'services_by_type': services_by_type
    })


# Галерея
def gallery_view(request):
    return render(request, 'gallery.html')


# Детали фото
def photo_detail_view(request, photo_id):
    return render(request, 'photo_detail.html', {'photo_id': photo_id})


# Кастомный логин
class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = CustomAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        start_time = time.time()

        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=username, password=password)

        if user is not None:
            login(self.request, user)
            end_time = time.time()

            print(f"[DEBUG] Авторизация пользователя {username} заняла {end_time - start_time:.4f} секунд")

            # Обновляем last_login
            if hasattr(user, 'last_login'):
                from django.utils import timezone
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])

            messages.success(self.request, f'Добро пожаловать, {user.username}!')
            return super().form_valid(form)

        return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['total_users'] = User.objects.count()
        except:
            context['total_users'] = 0
        return context


# Регистрация
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            start_time = time.time()

            # Сохранение пользователя в базу данных
            user = form.save()

            # Автоматический вход после регистрации
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                end_time = time.time()

                print(f"[DEBUG] Регистрация пользователя {username} заняла {end_time - start_time:.4f} секунд")
                print(f"[DEBUG] Создан пользователь с ID: {user.id}")

                messages.success(request, f'Аккаунт успешно создан для {username}!')
                return redirect('../home')
    else:
        form = CustomUserCreationForm()

    try:
        total_users = User.objects.count()
    except:
        total_users = 0

    context = {
        'form': form,
        'total_users': total_users,
    }
    return render(request, 'register.html', context)


# Страница профиля
@login_required
def profile_view(request):
    user = request.user

    # Получаем дополнительные данные о пользователе
    from django.utils import timezone
    from datetime import timedelta

    if hasattr(user, 'date_joined') and user.date_joined:
        days_registered = (timezone.now() - user.date_joined).days
    else:
        days_registered = 0

    # Если пользователь сохранил профиль
    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        if email and email != user.email:
            # Проверяем, не занят ли email другим пользователем
            from django.contrib.auth.models import User
            if not User.objects.filter(email=email).exclude(id=user.id).exists():
                user.email = email
                user.save()
                messages.success(request, 'Email успешно обновлен!')
            else:
                messages.error(request, 'Этот email уже используется другим пользователем')

        if first_name != user.first_name:
            user.first_name = first_name
            user.save()

        if last_name != user.last_name:
            user.last_name = last_name
            user.save()

        if first_name or last_name:
            messages.success(request, 'Профиль обновлен!')

    context = {
        'user': user,
        'days_registered': days_registered,
        'is_admin': user.is_superuser,
        'is_staff': user.is_staff,
    }

    return render(request, 'profile.html', context)


# Список пользователей (только для админов)
@login_required
def users_list_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для просмотра этой страницы')
        return redirect('home')

    users = User.objects.all().order_by('-date_joined')
    return render(request, 'users_list.html', {'users': users})


# Тест базы данных
def db_test_view(request):
    """Страница для тестирования работы с базой данных"""
    from django.db import connection

    try:
        user_count = User.objects.count()
        recent_users = User.objects.order_by('-date_joined')[:5]
        has_db = True
    except Exception as e:
        user_count = 0
        recent_users = []
        has_db = False
        error = str(e)

    # Показать SQL запросы (если DEBUG = True)
    queries = connection.queries if hasattr(connection, 'queries') else []

    context = {
        'user_count': user_count,
        'recent_users': recent_users,
        'has_db': has_db,
        'queries': queries[-10:],  # Последние 10 запросов
        'total_queries': len(queries),
    }

    if not has_db:
        context['error'] = error

    return render(request, 'db_test.html', context)


def custom_logout_view(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f'Вы успешно вышли из системы. До свидания, {username}!')
    return redirect('/home/')