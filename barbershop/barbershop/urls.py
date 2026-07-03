# my_project/urls.py
from django.contrib import admin
from django.urls import path, include  # Обязательно импортируй include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Подключаем все урлы из нашего приложения booking
    path('', include('barbers.urls')),
]