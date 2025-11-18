from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from .models import Service
# Create your views here.


def home(request):
    return render(request, 'home.html')


def photo_detail(request, photo_id):
    photo_id = int(photo_id)

    prev_photo_id = photo_id - 1 if photo_id > 1 else 1
    next_photo_id = photo_id + 1 if photo_id < 9 else 9

    context = {
        'photo_id': photo_id,
    }

    return render(request, 'photo_detail.html', context)


class ServiceListView(ListView):

    model = Service
    template_name = 'prices.html'
    context_object_name = 'services'  # переопределяем имя переменной в шаблоне
    paginate_by = 6  # количество услуг на странице
    queryset = Service.objects.filter(is_active=True)  # только активные услуги

    def get_context_data(self, **kwargs):
        """
        Добавляем дополнительные данные в контекст
        """
        context = super().get_context_data(**kwargs)
        # Группируем услуги по типам для удобного отображения
        services_by_type = {}
        for service in context['services']:
            if service.service_type not in services_by_type:
                services_by_type[service.service_type] = []
            services_by_type[service.service_type].append(service)

        context['services_by_type'] = services_by_type
        return context

def login(request):
    return render(request, 'login.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()

    return render(request, 'register.html', {'form': form})
