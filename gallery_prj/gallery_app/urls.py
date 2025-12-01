from django.urls import path
from django.contrib.auth import views as auth_views  # импортируем auth_views
from . import views
from .views import CustomLoginView

app_name = 'gallery'

urlpatterns = [
    # Основные страницы
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home'),
    path('prices/', views.prices_view, name='prices'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('gallery/photo/<int:photo_id>/', views.photo_detail_view, name='photo_detail'),

    # Аутентификация
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
]