from django.urls import path
from django.contrib.auth import views as auth_views  # импортируем auth_views
from . import views
from .views import CustomLoginView

app_name = 'gallery'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('home/', views.home_view, name='home'),
    path('prices/', views.prices_view, name='prices'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('gallery/photo/<int:photo_id>/', views.photo_detail_view, name='photo_detail'),


    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', views.custom_logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),


    path('booking/create/', views.create_booking, name='create_booking'),
    path('booking/my/', views.user_bookings, name='user_bookings'),
    path('booking/<uuid:booking_id>/cancel/', views.cancel_booking, name='cancel_booking'),
    path('booking/<uuid:booking_id>/delete/', views.delete_booking, name='delete_booking'),


    path('admin/bookings/', views.admin_booking_list, name='admin_booking_list'),
    path('admin/bookings/<uuid:booking_id>/', views.admin_booking_detail, name='admin_booking_detail'),
    path('admin/calendar/', views.admin_calendar_view, name='admin_calendar'),

]