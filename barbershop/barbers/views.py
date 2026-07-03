import json
import calendar as calendar_module
from datetime import datetime, timedelta, date
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import MasterProfile, Appointment, WorkSchedule, User, Service, MasterOffDay

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import logout as django_logout
from .models import MasterProfile

@login_required(login_url='/master/login/')
def master_page(request):
    """
    Отображает кабинет мастера. Доступно только после авторизации.
    Автоматически определяет master_id текущего пользователя.
    """
    # Проверяем, есть ли у пользователя профиль мастера
    try:
        master_profile = MasterProfile.objects.get(user=request.user)
    except MasterProfile.DoesNotExist:
        # Если зашел админ или клиент без профиля мастера, отдаем ошибку или редирект
        return render(request, 'barbers/master.html', {'error': 'Вы зашли как администратор/пользователь, но у вас нет профиля мастера.'})

    return render(request, 'barbers/master.html', {'master_id': master_profile.id, 'master_name': request.user.get_full_name() or request.user.username})


def master_logout(request):
    """Логаут для мастера и редирект на главную"""
    django_logout(request)
    return redirect('index')

def index_page(request):
    """Отображает главную страницу записи для клиента"""
    return render(request, 'index.html') # или 'index.html', смотря куда перенёс

# ==========================================
# 1. СЛУЖЕБНАЯ ФУНКЦИЯ ДЛЯ УВЕДОМЛЕНИЙ (Будущая логика)
# ==========================================
def send_appointment_notifications(appointment):
    """
    Сюда мы позже пропишем реальные запросы к API WhatsApp и Telegram.
    Пока это просто заглушка, которая выведет текст в консоль сервера.
    """
    client_name = appointment.client.first_name
    client_phone = appointment.client.phone
    master_name = appointment.master.user.get_full_name() or appointment.master.user.username
    service_name = appointment.service.name
    date_str = appointment.date.strftime('%d.%m.%Y')
    time_str = appointment.time_slot.strftime('%H:%M')

    # Текст для клиента (в WhatsApp)
    whatsapp_text = f"Привет, {client_name}! Вы записаны на услугу '{service_name}' к мастеру {master_name}. Ждем вас {date_str} в {time_str}."
    
    # Текст для мастера (в Telegram)
    telegram_text = f"🔥 Новая запись!\nУслуга: {service_name}\nКлиент: {client_name} ({client_phone})\nДата: {date_str} в {time_str}"

    print("\n--- [ОТПРАВКА УВЕДОМЛЕНИЙ] ---")
    print(f"Имитация WhatsApp для КЛИЕНТА ({client_phone}): {whatsapp_text}")
    print(f"Имитация Telegram для МАСТЕРА: {telegram_text}")
    print("---------------------------------\n")


# ==========================================
# 2. РАСЧЁТ ДОСТУПНОСТИ ДНЯ (общий хелпер для слотов и календаря)
# ==========================================
def compute_day_availability(master_id, target_date):
    """
    Возвращает (status, available_slots, message) для одного мастера на одну дату.
    status: 'off' (не работает / выходной), 'full' (рабочий день, но всё занято),
            'available' (есть свободные слоты), 'past' (дата уже прошла)
    """
    if target_date < datetime.today().date():
        return 'past', [], 'Нельзя записаться на прошедшую дату'

    weekday = target_date.isoweekday()

    # 1. Работает ли мастер в этот день недели вообще (недельный график)
    try:
        schedule = WorkSchedule.objects.get(master_id=master_id, day_of_week=weekday)
    except WorkSchedule.DoesNotExist:
        from datetime import time

        class TempSchedule:
            start_time = time(9, 0)
            end_time = time(18, 0)

        schedule = TempSchedule()

    # 2. Не взял ли мастер этот конкретный день целиком как выходной
    if MasterOffDay.objects.filter(master_id=master_id, date=target_date, start_time__isnull=True).exists():
        return 'off', [], 'Этот день у мастера отмечен как выходной'

    # 3. Частичные выходные (например, отгул с 12:00 до 15:00)
    partial_off_periods = list(MasterOffDay.objects.filter(
        master_id=master_id, date=target_date, start_time__isnull=False
    ).values_list('start_time', 'end_time'))

    # 4. Уже занятые слоты
    existing_appointments = Appointment.objects.filter(
        master_id=master_id,
        date=target_date,
        status__in=['pending', 'confirmed']
    ).values_list('time_slot', flat=True)
    busy_slots = {t.strftime('%H:%M') for t in existing_appointments}

    # 5. Генерируем сетку времени с шагом 30 минут
    available_slots = []
    current_time = datetime.combine(target_date, schedule.start_time)
    end_time = datetime.combine(target_date, schedule.end_time)
    now = datetime.now()

    while current_time < end_time:
        slot_time = current_time.time()
        slot_str = current_time.strftime('%H:%M')

        in_partial_off = any(start <= slot_time < end for start, end in partial_off_periods)
        is_past_today = target_date == now.date() and current_time.time() < now.time()

        if slot_str not in busy_slots and not in_partial_off and not is_past_today:
            available_slots.append(slot_str)

        current_time += timedelta(minutes=30)

    if not available_slots:
        return 'full', [], 'На эту дату нет свободного времени'

    return 'available', available_slots, None


# ==========================================
# 2.1 ПОЛУЧЕНИЕ СВОБОДНЫХ СЛОТОВ НА ДЕНЬ (ДЛЯ КЛИЕНТА)
# ==========================================
def get_available_slots(request, master_id):
    """
    Принимает GET-запрос с параметром ?date=YYYY-MM-DD
    Возвращает массив строк со свободным временем, например: ["10:00", "10:30", ...]
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Метод не поддерживается. Используйте GET'}, status=405)

    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'Параметр ?date=YYYY-MM-DD обязателен'}, status=400)

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Неверный формат даты. Используйте YYYY-MM-DD'}, status=400)

    status, available_slots, message = compute_day_availability(master_id, target_date)

    return JsonResponse({
        'master_id': master_id,
        'date': date_str,
        'status': status,
        'available_slots': available_slots,
        'message': message
    })


# ==========================================
# 2.2 ДОСТУПНОСТЬ МАСТЕРА НА ВЕСЬ МЕСЯЦ (ДЛЯ КАЛЕНДАРЯ КЛИЕНТА)
# ==========================================
def get_month_availability(request, master_id):
    """
    Принимает GET-параметры ?year=YYYY&month=MM
    Возвращает статус каждого дня месяца: 'off' | 'full' | 'available' | 'past'
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Метод не поддерживается. Используйте GET'}, status=405)

    try:
        year = int(request.GET.get('year'))
        month = int(request.GET.get('month'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'Параметры year и month обязательны и должны быть числами'}, status=400)

    if not MasterProfile.objects.filter(id=master_id).exists():
        return JsonResponse({'error': 'Мастер не найден'}, status=404)

    days_in_month = calendar_module.monthrange(year, month)[1]
    days_status = {}

    for day in range(1, days_in_month + 1):
        target_date = date(year, month, day)
        status, _, _ = compute_day_availability(master_id, target_date)
        days_status[target_date.strftime('%Y-%m-%d')] = status

    return JsonResponse({'master_id': master_id, 'year': year, 'month': month, 'days': days_status})


# ==========================================
# 3. СОЗДАНИЕ ЗАПИСИ (ДЛЯ КЛИЕНТА)
# ==========================================
@csrf_exempt  # Включаем для тестов через Postman без CSRF-токена
def create_appointment(request):
    """
    Принимает POST-запрос с JSON телом:
    {
        "name": "Аскар",
        "phone": "+77071112233",
        "master_id": 1,
        "service_id": 2,
        "date": "2026-07-05",
        "time_slot": "14:30"
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается. Используйте POST'}, status=405)

    try:
        data = json.loads(request.body)
        
        # Проверяем наличие всех обязательных полей
        required_fields = ['name', 'phone', 'master_id', 'service_id', 'date', 'time_slot']
        if not all(field in data for field in required_fields):
            return JsonResponse({'error': 'Заполнены не все обязательные поля'}, status=400)

        # 1. Защита "от дурака": Проверяем, не заняли ли это время, пока клиент думал
        appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        appointment_time = datetime.strptime(data['time_slot'], '%H:%M').time()
        is_taken = Appointment.objects.filter(
            master_id=data['master_id'],
            date=appointment_date,
            time_slot=appointment_time,
            status__in=['pending', 'confirmed']
        ).exists()

        if is_taken:
            return JsonResponse({'error': 'Извините, это время уже только что забронировали'}, status=400)

        # 2. Находим клиента по телефону или автоматически регистрируем нового
        client, created = User.objects.get_or_create(
            phone=data['phone'],
            defaults={
                'username': data['phone'],  # username должен быть уникальным, телефон подходит идеально
                'first_name': data['name'],
                'role': 'client'
            }
        )

        # 3. Создаем саму запись в БД
        appointment = Appointment.objects.create(
            client=client,
            master_id=data['master_id'],
            service_id=data['service_id'],
            date=appointment_date,
            time_slot=appointment_time,
            status='pending'
        )

        # 4. Запускаем отправку уведомлений
        send_appointment_notifications(appointment)

        return JsonResponse({
            'status': 'success',
            'appointment_id': appointment.id,
            'message': 'Вы успешно записаны!'
        }, status=201)

    except Exception as e:
        return JsonResponse({'error': f'Что-то пошло не так: {str(e)}'}, status=500)
    
# ==========================================
# 4. ЛИЧНЫЙ КАБИНЕТ МАСТЕРА: СПИСОК ЕГО ЗАПИСЕЙ
# ==========================================
def get_master_appointments(request, master_id):
    """
    Возвращает список всех записей к конкретному мастеру.
    Можно передать фильтр ?date=YYYY-MM-DD, чтобы увидеть записи только на определенный день.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Метод не поддерживается. Используйте GET'}, status=405)

    try:
        master_profile = MasterProfile.objects.get(id=master_id)
    except MasterProfile.DoesNotExist:
        return JsonResponse({'error': 'Мастер не найден'}, status=404)

    # Берём записи этого мастера
    appointments = Appointment.objects.filter(master=master_profile)

    # Если в URL передали конкретную дату, фильтруем по ней
    date_str = request.GET.get('date')
    if date_str:
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            appointments = appointments.filter(date=target_date)
        except ValueError:
            return JsonResponse({'error': 'Неверный формат даты. Используйте YYYY-MM-DD'}, status=400)

    # Сортируем по дате и времени, чтобы список шёл по порядку
    appointments = appointments.order_by('date', 'time_slot')

    # Формируем красивый список для отправки на фронтенд
    appointments_list = []
    for app in appointments:
        appointments_list.append({
            'id': app.id,
            'client_name': app.client.first_name if app.client else "Удаленный клиент",
            'client_phone': app.client.phone if app.client else "",
            'service_name': app.service.name,
            'service_duration': app.service.duration_minutes,
            'date': app.date.strftime('%Y-%m-%d'),
            'time': app.time_slot.strftime('%H:%M'),
            'status': app.status,
            'status_display': app.get_status_display() # Вернет "Ожидает подтверждения", "Подтверждена" и т.д.
        })

    return JsonResponse({'master_id': master_id, 'appointments': appointments_list})


# ==========================================
# 5. ЛИЧНЫЙ КАБИНЕТ МАСТЕРА: УПРАВЛЕНИЕ ВЫХОДНЫМИ (БАТЧ/ПАКЕТНАЯ ОБРАБОТКА)
# ==========================================
@csrf_exempt
def toggle_off_day(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается. Используйте POST'}, status=405)
    try:
        data = json.loads(request.body)
        master_id = data.get('master_id')
        date_str = data.get('date')

        if not master_id or not date_str:
            return JsonResponse({'error': 'Параметры master_id и date обязательны'}, status=400)

        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        off_day_query = MasterOffDay.objects.filter(master_id=master_id, date=target_date)

        if off_day_query.exists():
            off_day_query.delete()
            return JsonResponse({'status': 'success', 'message': 'День снова сделан РАБОЧИМ'})
        else:
            MasterOffDay.objects.create(master_id=master_id, date=target_date)
            return JsonResponse({'status': 'success', 'message': 'День успешно заблокирован (ВЫХОДНОЙ)'})
    except Exception as e:
        return JsonResponse({'error': f'Ошибка: {str(e)}'}, status=500)

@csrf_exempt
def bulk_toggle_off_days(request):
    """
    POST-запрос для пакетного добавления/удаления выходных дней мастера.
    Тело JSON:
    {
        "master_id": 1,
        "dates": ["2026-07-05", "2026-07-06", "2026-07-10"]
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается. Используйте POST'}, status=405)

    try:
        data = json.loads(request.body)
        master_id = data.get('master_id')
        dates_list = data.get('dates')  # Получаем массив строк-дат

        if not master_id or dates_list is None:
            return JsonResponse({'error': 'Параметры master_id и dates обязательны'}, status=400)

        try:
            master_profile = MasterProfile.objects.get(id=master_id)
        except MasterProfile.DoesNotExist:
            return JsonResponse({'error': 'Мастер не найден'}, status=404)

        processed_dates = []
        for date_str in dates_list:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                continue # Если прилетела битая дата, просто пропускаем её

            # Переключаем статус дня:
            off_day_query = MasterOffDay.objects.filter(master=master_profile, date=target_date)

            if off_day_query.exists():
                # Если уже был заблокирован — удаляем выходной (делаем рабочим)
                off_day_query.delete()
            else:
                # Если не был выходным — блокируем день полностью
                MasterOffDay.objects.create(master=master_profile, date=target_date)
            
            processed_dates.append(date_str)

        return JsonResponse({
            'status': 'success', 
            'message': f'Статус успешно изменен для {len(processed_dates)} дат.',
            'processed_dates': processed_dates
        })

    except Exception as e:
        return JsonResponse({'error': f'Ошибка на сервере: {str(e)}'}, status=500)

# ==========================================
# 5.1 ПОЛУЧЕНИЕ ВСЕХ ВЫХОДНЫХ МАСТЕРА (ДЛЯ КАЛЕНДАРЯ)
# ==========================================
def get_master_off_days(request, master_id):
    """
    Возвращает список всех дат (YYYY-MM-DD), которые отмечены как выходные у мастера.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Метод не поддерживается. Используйте GET'}, status=405)

    try:
        master_profile = MasterProfile.objects.get(id=master_id)
    except MasterProfile.DoesNotExist:
        return JsonResponse({'error': 'Мастер не найден'}, status=404)

    # Выбираем даты выходных
    off_days = MasterOffDay.objects.filter(master=master_profile, start_time__isnull=True).values_list('date', flat=True)
    
    # Явно принудительно форматируем каждую дату в YYYY-MM-DD строковый тип
    dates_list = [d.strftime('%Y-%m-%d') for d in off_days]

    return JsonResponse({'master_id': master_id, 'off_dates': dates_list})

# ==========================================
# 6. ПОЛУЧЕНИЕ СПИСКА ВСЕХ УСЛУГ (ДЛЯ КЛИЕНТА)
# ==========================================
def get_services(request):
    """
    Возвращает список всех услуг барбершопа для первого шага записи.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Метод не поддерживается. Используйте GET'}, status=405)

    services = Service.objects.all()
    services_list = []
    
    for s in services:
        services_list.append({
            'id': s.id,
            'name': s.name,
            'price': float(s.price),
            'duration_minutes': s.duration_minutes
        })

    return JsonResponse({'services': services_list})


# ==========================================
# 7. ПОЛУЧЕНИЕ СПИСКА ВСЕХ МАСТЕРОВ (ДЛЯ КЛИЕНТА)
# ==========================================
def get_masters(request):
    service_id = request.GET.get('service_id')

    masters = MasterProfile.objects.select_related('user')

    if service_id and service_id.isdigit():
        masters = masters.filter(
            services__id=int(service_id),
            is_active=True
        )

    return JsonResponse({
        'masters': [
            {
                'master_id': m.id,
                'name': m.user.get_full_name() or m.user.username,
                'bio': m.bio,
            }
            for m in masters
        ]
    })


# ==========================================
# 8. НЕДЕЛЬНЫЙ ГРАФИК РАБОТЫ МАСТЕРА (САМОСТОЯТЕЛЬНАЯ НАСТРОЙКА)
# ==========================================
def get_work_schedule(request, master_id):
    """
    Возвращает текущий недельный график мастера.
    Формат: {"1": {"start": "09:00", "end": "18:00"}, "3": {...}, ...}
    День недели, отсутствующий в ответе, считается нерабочим.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Метод не поддерживается. Используйте GET'}, status=405)

    if not MasterProfile.objects.filter(id=master_id).exists():
        return JsonResponse({'error': 'Мастер не найден'}, status=404)

    schedule = {}
    for row in WorkSchedule.objects.filter(master_id=master_id):
        schedule[str(row.day_of_week)] = {
            'start': row.start_time.strftime('%H:%M'),
            'end': row.end_time.strftime('%H:%M')
        }

    return JsonResponse({'master_id': master_id, 'schedule': schedule})


@csrf_exempt
def update_work_schedule(request, master_id):
    """
    Сохраняет недельный график мастера.
    Тело JSON:
    {
        "days": [
            {"day_of_week": 1, "is_working": true, "start_time": "09:00", "end_time": "18:00"},
            {"day_of_week": 2, "is_working": false},
            ...
        ]
    }
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не поддерживается. Используйте POST'}, status=405)

    try:
        master_profile = MasterProfile.objects.get(id=master_id)
    except MasterProfile.DoesNotExist:
        return JsonResponse({'error': 'Мастер не найден'}, status=404)

    try:
        data = json.loads(request.body)
        days = data.get('days', [])

        for day_data in days:
            day_of_week = day_data.get('day_of_week')
            is_working = day_data.get('is_working')

            if day_of_week is None or is_working is None:
                continue

            if is_working:
                start_str = day_data.get('start_time')
                end_str = day_data.get('end_time')
                if not start_str or not end_str:
                    continue

                start_time = datetime.strptime(start_str, '%H:%M').time()
                end_time = datetime.strptime(end_str, '%H:%M').time()

                if start_time >= end_time:
                    return JsonResponse({'error': f'Время начала должно быть раньше окончания (день {day_of_week})'}, status=400)

                WorkSchedule.objects.update_or_create(
                    master=master_profile,
                    day_of_week=day_of_week,
                    defaults={'start_time': start_time, 'end_time': end_time}
                )
            else:
                WorkSchedule.objects.filter(master=master_profile, day_of_week=day_of_week).delete()

        return JsonResponse({'status': 'success', 'message': 'График работы сохранён'})

    except Exception as e:
        return JsonResponse({'error': f'Ошибка на сервере: {str(e)}'}, status=500)