from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.contrib.auth.admin import UserAdmin as UnfoldUserAdmin  # type: ignore <--- Игнорим придирки Pylance
from .models import User, Service, MasterProfile, WorkSchedule, MasterOffDay, Appointment

@admin.register(User)
class CustomUserAdmin(UnfoldUserAdmin):  # <--- Меняем обратно на UnfoldUserAdmin
    list_display = ('username', 'first_name', 'phone', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    
    # Расширяем стандартные поля UnfoldUserAdmin, добавляя твои кастомные
    fieldsets = UnfoldUserAdmin.fieldsets + (
        ('Дополнительные поля ролей', {'fields': ('role', 'phone', 'tg_chat_id')}),
    )
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