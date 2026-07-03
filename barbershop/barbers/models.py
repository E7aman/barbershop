from django.contrib.auth.models import AbstractUser
from django.db import models


# 1. КАСТОМНЫЙ ПОЛЬЗОВАТЕЛЬ (Управление ролями)
class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Администратор'),
        ('master', 'Мастер'),
        ('client', 'Клиент'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True, null=True, unique=True, verbose_name="Номер телефона")
    tg_chat_id = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telegram Chat ID для уведомлений")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


# 2. УСЛУГИ (Что предоставляет бизнес)
class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название услуги")
    description = models.TextField(blank=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    duration_minutes = models.IntegerField(default=30, verbose_name="Длительность (в минутах)")

    def __str__(self):
        return f"{self.name} — {self.price} руб."


# 3. ПРОФИЛЬ МАСТЕРА (Дополнительные данные для мастера)
class MasterProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        limit_choices_to={'role': 'master'}, 
        related_name='master_profile'
    )
    services = models.ManyToManyField(Service, related_name='masters', verbose_name="Услуги, которые оказывает")
    is_active = models.BooleanField(default=True, verbose_name="Работает ли еще в компании")
    bio = models.TextField(blank=True, null=True, verbose_name="О мастере (отображается клиентам)")

    def __str__(self):
        return f"Мастер: {self.user.get_full_name() or self.user.username}"


# 4. РАСПИСАНИЕ И ВЫХОДНЫЕ
class WorkSchedule(models.Model):
    """Постоянный график (например, каждый Пн с 9:00 до 18:00)"""
    WEEKDAYS = (
        (1, 'Понедельник'),
        (2, 'Вторник'),
        (3, 'Среда'),
        (4, 'Четверг'),
        (5, 'Пятница'),
        (6, 'Суббота'),
        (7, 'Воскресенье'),
    )
    master = models.ForeignKey(MasterProfile, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.IntegerField(choices=WEEKDAYS, verbose_name="День недели")
    start_time = models.TimeField(verbose_name="Начало работы")
    end_time = models.TimeField(verbose_name="Конец работы")

    class Meta:
        unique_together = ('master', 'day_of_week') # Чтобы нельзя было создать два Пн для одного мастера


class MasterOffDay(models.Model):
    """Конкретные даты, когда мастер не может работать (отпуск, больничный)"""
    master = models.ForeignKey(MasterProfile, on_delete=models.CASCADE, related_name='off_days')
    date = models.DateField(verbose_name="Дата выходного")
    start_time = models.TimeField(blank=True, null=True, verbose_name="С какого времени (если не весь день)")
    end_time = models.TimeField(blank=True, null=True, verbose_name="По какое время")

    def __str__(self):
        return f"Выходной у {self.master} на {self.date}"


# 5.ЗАПИСИ (Главная сущность для CRUD)
class Appointment(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Ожидает подтверждения'),
        ('confirmed', 'Подтверждена'),
        ('canceled', 'Отменена'),
        ('completed', 'Завершена'),
    )
    
    client = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        limit_choices_to={'role': 'client'}, 
        related_name='appointments',
        verbose_name="Клиент"
    )
    master = models.ForeignKey(MasterProfile, on_delete=models.CASCADE, related_name='appointments', verbose_name="Мастер")
    service = models.ForeignKey(Service, on_delete=models.PROTECT, verbose_name="Услуга") # PROTECT не даст удалить услугу, если на нее есть запись
    
    date = models.DateField(verbose_name="Дата визита")
    time_slot = models.TimeField(verbose_name="Время визита")
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending', verbose_name="Статус записи")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Запись {self.id}: {self.client} к {self.master} на {self.date} {self.time_slot}"