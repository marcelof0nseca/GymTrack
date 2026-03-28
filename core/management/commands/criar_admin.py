from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Cria um superusuário automaticamente'

    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = os.environ.get('ADMIN_USERNAME')
        email = os.environ.get('ADMIN_EMAIL')
        password = os.environ.get('ADMIN_PASSWORD')

        if not username or not password:
            self.stdout.write(self.style.WARNING('ADMIN_USERNAME ou ADMIN_PASSWORD não definidos.'))
            return

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS('Superusuário já existe.'))
            return

        User.objects.create_superuser(
            username=username,
            email=email or '',
            password=password
        )

        self.stdout.write(self.style.SUCCESS('Superusuário criado com sucesso!'))