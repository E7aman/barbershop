from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Автоматически создает суперпользователя, если его еще нет'

    def handle(self, *args, **options):
        User = get_user_model()
        username = 'admin'
        email = 'admin@example.com'
        password = 'adminpassword123'  # <--- Поменяй пароль на свой

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username, 
                email=email, 
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Суперпользователь "{username}" успешно создан!'))
        else:
            self.stdout.write(self.style.WARNING(f'Пользователь "{username}" уже существует.'))