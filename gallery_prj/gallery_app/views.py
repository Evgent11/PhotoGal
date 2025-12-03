from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import CustomUserCreationForm, CustomAuthenticationForm
import time
from django.contrib.auth import logout
from django.utils import timezone
from .forms import BookingForm, AdminBookingForm
import datetime
from django.core.paginator import Paginator
from .models import Booking, Service
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q

def home_view(request):
    try:
        user_count = User.objects.count()
    except:
        user_count = 0

    context = {
        'user_count': user_count,
    }
    return render(request, 'home.html', context)



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



def gallery_view(request):
    return render(request, 'gallery.html')



def photo_detail_view(request, photo_id):
    return render(request, 'photo_detail.html', {'photo_id': photo_id})



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



def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)

        if form.is_valid():
            start_time = time.time()

            user = form.save()

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



@login_required
def profile_view(request):
    user = request.user


    from django.utils import timezone
    from datetime import timedelta

    if hasattr(user, 'date_joined') and user.date_joined:
        days_registered = (timezone.now() - user.date_joined).days
    else:
        days_registered = 0


    if request.method == 'POST':
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        if email and email != user.email:

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


@login_required()
def users_list_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'У вас нет прав для просмотра этой страницы')
        return redirect('home')

    users = User.objects.all().order_by('-date_joined')
    return render(request, 'users_list.html', {'users': users})


def custom_logout_view(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
    return redirect('/home/')

@login_required
def user_bookings(request):
    """Список бронирований пользователя"""
    bookings = Booking.objects.filter(user=request.user).order_by('-created_at')

    # Фильтрация по статусу
    status_filter = request.GET.get('status')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    # Пагинация
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Статистика
    stats = {
        'total': bookings.count(),
        'pending': bookings.filter(status='pending').count(),
        'confirmed': bookings.filter(status='confirmed').count(),
        'upcoming': bookings.filter(
            status='confirmed',
            booking_date__gte=timezone.now().date()
        ).count(),
    }

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'title': 'Мои бронирования',
    }
    return render(request, 'user_bookings.html', context)





def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_admin)
def admin_booking_list(request):
    """Список всех бронирований для администратора"""
    bookings = Booking.objects.all().order_by('-created_at')

    # Фильтрация
    status_filter = request.GET.get('status')
    date_filter = request.GET.get('date')
    search_query = request.GET.get('search')

    if status_filter:
        bookings = bookings.filter(status=status_filter)

    if date_filter:
        try:
            filter_date = datetime.datetime.strptime(date_filter, '%Y-%m-%d').date()
            bookings = bookings.filter(booking_date=filter_date)
        except ValueError:
            pass

    if search_query:
        bookings = bookings.filter(
            Q(client_name__icontains=search_query) |
            Q(client_phone__icontains=search_query) |
            Q(client_email__icontains=search_query) |
            Q(service__name__icontains=search_query)
        )

    # Пагинация
    paginator = Paginator(bookings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Статистика
    today = timezone.now().date()
    stats = {
        'total': Booking.objects.count(),
        'pending': Booking.objects.filter(status='pending').count(),
        'today': Booking.objects.filter(booking_date=today, status='confirmed').count(),
        'upcoming': Booking.objects.filter(
            booking_date__gte=today,
            status='confirmed'
        ).count(),
        'revenue': sum(b.get_total_price() for b in Booking.objects.filter(
            status__in=['confirmed', 'completed']
        ) if b.get_total_price()),
    }

    context = {
        'page_obj': page_obj,
        'stats': stats,
        'filters': {
            'status': status_filter,
            'date': date_filter,
            'search': search_query,
        },
        'title': 'Управление бронированиями',
    }
    return render(request, 'booking/admin_list.html', context)

@login_required
@user_passes_test(is_admin)
def admin_booking_detail(request, booking_id):
    """Детальная информация о бронировании для администратора"""
    booking = get_object_or_404(Booking, id=booking_id)

    if request.method == 'POST':
        form = AdminBookingForm(request.POST, instance=booking)
        if form.is_valid():
            updated_booking = form.save(commit=False)

            # Если статус изменился на confirmed/rejected/completed, сохраняем администратора
            if form.has_changed() and 'status' in form.changed_data:
                updated_booking.admin_user = request.user

            updated_booking.save()

            messages.success(request, 'Бронирование обновлено.')

            # Отправка уведомления пользователю при изменении статуса
            if 'status' in form.changed_data:
                # send_booking_status_update_email(booking)
                pass

            return redirect('admin_booking_detail', booking_id=booking_id)
    else:
        form = AdminBookingForm(instance=booking)

    # История изменений (можно добавить модель History позже)
    # history = BookingHistory.objects.filter(booking=booking).order_by('-created_at')

    context = {
        'booking': booking,
        'form': form,
        # 'history': history,
        'title': f'Бронирование #{booking.id}',
    }
    return render(request, 'booking/admin_detail.html', context)

@login_required
@user_passes_test(is_admin)
def admin_calendar_view(request):

    year = request.GET.get('year')
    month = request.GET.get('month')

    if year and month:
        try:
            year = int(year)
            month = int(month)
        except ValueError:
            year = timezone.now().year
            month = timezone.now().month
    else:
        year = timezone.now().year
        month = timezone.now().month

    start_date = datetime.date(year, month, 1)
    if month == 12:
        end_date = datetime.date(year + 1, 1, 1)
    else:
        end_date = datetime.date(year, month + 1, 1)

    bookings = Booking.objects.filter(
        booking_date__gte=start_date,
        booking_date__lt=end_date,
        status='confirmed'
    ).order_by('booking_date', 'booking_time')

    bookings_by_day = {}
    for booking in bookings:
        day = booking.booking_date.day
        if day not in bookings_by_day:
            bookings_by_day[day] = []
        bookings_by_day[day].append(booking)

    import calendar
    cal = calendar.monthcalendar(year, month)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    context = {
        'calendar': cal,
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'bookings_by_day': bookings_by_day,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': timezone.now().date(),
        'title': 'Календарь бронирований',
    }
    return render(request, 'booking/admin_calendar.html', context)

@login_required
def create_booking(request):
    """Создание нового бронирования"""
    if request.method == 'POST':
        form = BookingForm(request.POST, request=request)
        if form.is_valid():
            booking = form.save(commit=False)

            # Если пользователь авторизован, привязываем его
            if request.user.is_authenticated:
                booking.user = request.user

            # Если пользователь не указал email, используем email из аккаунта
            if not booking.client_email and request.user.is_authenticated:
                booking.client_email = request.user.email

            booking.save()

            messages.success(request,
                             '✅ Бронирование успешно создано! '
                             'Мы свяжемся с вами в течение 24 часов для подтверждения.'
                             )

            return redirect('/booking/my/')  # Изменено на абсолютный путь
        else:
            # Если форма невалидна, показываем ошибки
            available_dates = Booking.get_available_dates()
            return render(request, 'create_booking.html', {
                'form': form,
                'available_dates': available_dates
            })
    else:
        # GET запрос - показываем пустую форму
        form = BookingForm(request=request)
        available_dates = get_available_dates()
        return render(request, 'create_booking.html', {
            'form': form,
            'available_dates': available_dates
        })

@login_required
def delete_booking(request, booking_id):
    """Удаление бронирования"""
    booking = get_object_or_404(Booking, id=booking_id)

    # Проверяем, что пользователь имеет право удалять это бронирование
    if booking.user != request.user and not request.user.is_staff:
        return HttpResponseForbidden("У вас нет прав для удаления этого бронирования")

    # Проверяем статус бронирования (можно удалять только определенные статусы)
    if booking.status == 'completed':
        messages.error(request, "Нельзя удалить выполненное бронирование")
        return redirect('/booking/my/')  # Изменено на абсолютный путь

    if request.method == 'POST':
        # Удаляем бронирование
        booking.delete()

        # Показываем сообщение об успешном удалении
        messages.success(request, "Бронирование успешно удалено")

        # Перенаправляем обратно на страницу бронирований
        return redirect('/booking/my/')  # Изменено на абсолютный путь
    else:
        # GET запрос - показываем страницу подтверждения
        return render(request, 'delete_confirmation.html', {'booking': booking})

@login_required
def cancel_booking(request, booking_id):
    """Отмена бронирования пользователем"""
    try:
        booking = Booking.objects.get(id=booking_id, user=request.user)
    except Booking.DoesNotExist:
        messages.error(request, 'Бронирование не найдено.')
        return redirect('/booking/my/')  # Изменено на абсолютный путь

    # Проверяем условия отмены
    if booking.status not in ['pending', 'confirmed']:
        messages.error(request, 'Невозможно отменить бронирование с текущим статусом.')
        return redirect(f'/booking/{booking_id}/')  # Изменено на абсолютный путь

    if not booking.is_upcoming():
        messages.error(request, 'Невозможно отменить прошедшее бронирование.')
        return redirect(f'/booking/{booking_id}/')  # Изменено на абсолютный путь

    if booking.get_days_until() < 2:
        messages.error(request, 'Отмена возможна минимум за 48 часов до съемки.')
        return redirect(f'/booking/{booking_id}/')  # Изменено на абсолютный путь

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()

        messages.warning(request, 'Бронирование отменено.')
        # send_booking_cancellation_email(booking)  # Отправка уведомления

        return redirect('/booking/my/')  # Изменено на абсолютный путь

    # Если GET запрос, показываем страницу подтверждения
    return render(request, 'cancel_confirmation.html', {'booking': booking})

def get_available_dates():
    """Получение доступных дат для бронирования"""
    from datetime import timedelta

    available_dates = []
    today = timezone.now().date()

    # Бронирование доступно на 3 месяца вперед
    end_date = today + timedelta(days=90)

    current_date = today + timedelta(days=2)  # Минимум за 48 часов

    while current_date <= end_date:
        # Исключаем воскресенья
        if current_date.weekday() != 6:
            # Проверяем, не слишком ли много бронирований на этот день
            # (можно ограничить, например, 2 бронированиями в день)
            bookings_count = Booking.objects.filter(
                booking_date=current_date,
                status__in=['confirmed', 'pending']
            ).count()

            if bookings_count < 3:  # Максимум 3 съемки в день
                available_dates.append(current_date)

        current_date += timedelta(days=1)

    return available_dates


def check_date_availability(date):
    """Проверка доступности даты"""
    # Получаем все подтвержденные бронирования на эту дату
    bookings = Booking.objects.filter(
        booking_date=date,
        status__in=['confirmed']
    )
    total_hours = sum(booking.duration for booking in bookings)

    return total_hours < 8




