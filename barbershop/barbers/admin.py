from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin  # <--- Главный класс для красоты и кнопок
from .models import User, Service, MasterProfile, WorkSchedule, MasterOffDay, Appointment

# 1. Пользователи
@admin.register(User)
class CustomUserAdmin(UnfoldModelAdmin):
    list_display = ('username', 'first_name', 'phone', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    fields = ('username', 'first_name', 'last_name', 'email', 'role', 'phone', 'tg_chat_id', 'is_staff', 'is_active', 'is_superuser')

# 2. Записи (Appointments) — теперь тоже на UnfoldModelAdmin
@admin.register(Appointment)
class AppointmentAdmin(UnfoldModelAdmin):
    list_display = ('id', 'client', 'master', 'service', 'date', 'time_slot', 'status')
    list_filter = ('status', 'date', 'master')
    search_fields = ('client__phone', 'client__first_name')
    list_editable = ('status',)

# 3. Все остальные модели переводим на классы UnfoldModelAdmin
@admin.register(Service)
class ServiceAdmin(UnfoldModelAdmin):
    pass

@admin.register(MasterProfile)
class MasterProfileAdmin(UnfoldModelAdmin):
    pass

@admin.register(WorkSchedule)
class WorkScheduleAdmin(UnfoldModelAdmin):
    pass

@admin.register(MasterOffDay)
class MasterOffDayAdmin(UnfoldModelAdmin):
    pass