from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.shortcuts import redirect
from django.urls import reverse
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.decorators import action # <--- Не забудь импортировать декоратор
from .models import User, Service, MasterProfile, WorkSchedule, MasterOffDay, Appointment

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, UnfoldModelAdmin):
    list_display = ('username', 'first_name', 'phone', 'role', 'is_staff')
    list_filter = ('role', 'is_staff')
    
    # Выводим большую кнопку "Сменить пароль" в правый верхний угол страницы редактирования
    actions_detail = ["change_password_action"]

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительные поля ролей', {'fields': ('role', 'phone', 'tg_chat_id')}),
    )

    @action(description="Сменить пароль", url_path="change-password")
    def change_password_action(self, request, object_id):
        # Перенаправляем админа/клиента на стандартную защищенную форму смены пароля Django
        return redirect(reverse("admin:auth_user_password_change", args=[object_id]))

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