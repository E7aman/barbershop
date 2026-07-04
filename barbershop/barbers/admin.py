from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin as UnfoldModelAdmin  # <--- Импортируем базовый красивый класс Unfold
from .models import User, Service, MasterProfile, WorkSchedule, MasterOffDay, Appointment

# Регистрируем пользователя через базовый UnfoldModelAdmin, чтобы вернуть кнопку добавления
@admin.register(User)
class CustomUserAdmin(UnfoldModelAdmin):
    list_display = ('username', 'first_name', 'phone', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    
    # Так как мы наследуемся от ModelAdmin, поля редактирования настраиваем через fields
    fields = ('username', 'first_name', 'last_name', 'email', 'role', 'phone', 'tg_chat_id', 'is_staff', 'is_superuser')
# Выводим записи (самое главное для админа)
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'master', 'service', 'date', 'time_slot', 'status')
    list_filter = ('status', 'date', 'master')
    search_fields = ('client__phone', 'client__first_name')
    list_editable = ('status',) # Можно менять статус прямо из таблицы!

# Регистрируем остальное базово
admin.site.register(Service)
admin.site.register(MasterProfile)
admin.site.register(WorkSchedule)
admin.site.register(MasterOffDay)