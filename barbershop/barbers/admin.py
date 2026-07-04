from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from .models import User, Service, MasterProfile, WorkSchedule, MasterOffDay, Appointment

# Используем стандартный UserAdmin от Django, но добавляем обертку Unfold через миксин
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, UnfoldModelAdmin):  # <--- Магия множественного наследования
    list_display = ('username', 'first_name', 'phone', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    
    # Добавляем кастомные поля в стандартные филдсеты Django
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительные поля ролей', {'fields': ('role', 'phone', 'tg_chat_id')}),
    )

# 2. Записи (Appointments)
@admin.register(Appointment)
class AppointmentAdmin(UnfoldModelAdmin):
    list_display = ('id', 'client', 'master', 'service', 'date', 'time_slot', 'status')
    list_filter = ('status', 'date', 'master')
    search_fields = ('client__phone', 'client__first_name')
    list_editable = ('status',)

# 3. Все остальные модели
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