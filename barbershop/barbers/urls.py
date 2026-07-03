from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Главная (Форма записи клиента)
    path('', views.index_page, name='index'),
    
    # Кабинет мастера и Логин/Логаут системы
    path('master/', views.master_page, name='master_page'),
    path('login/', auth_views.LoginView.as_view(template_name='barbers/login.html'), name='master_login'),
    path('master/login/', auth_views.LoginView.as_view(template_name='barbers/login.html'), name='master_login'),
    path('master/logout/', views.master_logout, name='master_logout'),

    # API Эндпоинты
    path('api/services/', views.get_services, name='get_services'),
    path('api/masters/', views.get_masters, name='get_masters'),
    path('api/masters/<int:master_id>/slots/', views.get_available_slots, name='get_slots'),
    path('api/masters/<int:master_id>/month-availability/', views.get_month_availability, name='get_month_availability'),
    path('api/appointments/create/', views.create_appointment, name='create_appointment'),
    path('api/masters/<int:master_id>/appointments/', views.get_master_appointments, name='master_appointments'),
    path('api/masters/toggle-off-day/', views.toggle_off_day, name='toggle_off_day'),
    path('api/masters/<int:master_id>/off-days/', views.get_master_off_days, name='get_master_off_days'),
    path('api/masters/<int:master_id>/work-schedule/', views.get_work_schedule, name='get_work_schedule'),
    path('api/masters/<int:master_id>/work-schedule/update/', views.update_work_schedule, name='update_work_schedule'),

    # НОВЫЙ эндпоинт для пакетного выбора дат из календаря
    path('api/masters/bulk-toggle-off-days/', views.bulk_toggle_off_days, name='bulk_toggle_off_days'),
]