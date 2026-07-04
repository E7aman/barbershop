from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from unfold.admin import UserAdmin as UnfoldUserAdmin  # <--- Импортируем unfold-версию админки
from .models import User, Service, MasterProfile, WorkSchedule, MasterOffDay, Appointment

# Используем unfold'овский UserAdmin
@admin.register(User)
class CustomUserAdmin(UnfoldUserAdmin):
    list_display = ('username', 'first_name', 'phone', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    
    # Добавляем кастомные поля в филдсеты unfold
    fieldsets = UnfoldUserAdmin.fieldsets + (
        ('Дополнительные поля ролей', {'fields': ('role', 'phone', 'tg_chat_id')}),
    )
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