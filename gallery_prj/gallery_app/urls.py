from .views import *
from django.urls import path

app_name = 'gallery'

urlpatterns = [
    path('home/', home_view),
    path('photo/<int:photo_id>/', photo_detail_view, name='photo_detail'),
    path('prices/', ServiceListView.as_view()),
    path('login/', login),
    path('register/', register)
]