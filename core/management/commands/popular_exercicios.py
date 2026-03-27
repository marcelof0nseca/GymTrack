from django.core.management.base import BaseCommand
from core.models import ExercicioBase


class Command(BaseCommand):
    help = 'Popula o banco com exercícios base do sistema'

    def handle(self, *args, **kwargs):
        exercicios = [
            {"nome": "Supino reto", "grupo_muscular": "Peito"},
            {"nome": "Supino inclinado", "grupo_muscular": "Peito"},
            {"nome": "Crucifixo", "grupo_muscular": "Peito"},
            {"nome": "Peck deck", "grupo_muscular": "Peito"},

            {"nome": "Puxada frontal", "grupo_muscular": "Costas"},
            {"nome": "Remada curvada", "grupo_muscular": "Costas"},
            {"nome": "Remada baixa", "grupo_muscular": "Costas"},
            {"nome": "Pulldown", "grupo_muscular": "Costas"},

            {"nome": "Desenvolvimento militar", "grupo_muscular": "Ombro"},
            {"nome": "Elevação lateral", "grupo_muscular": "Ombro"},
            {"nome": "Elevação frontal", "grupo_muscular": "Ombro"},
            {"nome": "Crucifixo inverso", "grupo_muscular": "Ombro"},

            {"nome": "Rosca direta", "grupo_muscular": "Bíceps"},
            {"nome": "Rosca alternada", "grupo_muscular": "Bíceps"},
            {"nome": "Rosca martelo", "grupo_muscular": "Bíceps"},

            {"nome": "Tríceps pulley", "grupo_muscular": "Tríceps"},
            {"nome": "Tríceps francês", "grupo_muscular": "Tríceps"},
            {"nome": "Tríceps testa", "grupo_muscular": "Tríceps"},

            {"nome": "Agachamento livre", "grupo_muscular": "Pernas"},
            {"nome": "Leg press", "grupo_muscular": "Pernas"},
            {"nome": "Cadeira extensora", "grupo_muscular": "Pernas"},
            {"nome": "Mesa flexora", "grupo_muscular": "Pernas"},
            {"nome": "Stiff", "grupo_muscular": "Pernas"},
            {"nome": "Panturrilha em pé", "grupo_muscular": "Pernas"},

            {"nome": "Prancha", "grupo_muscular": "Abdômen"},
            {"nome": "Abdominal infra", "grupo_muscular": "Abdômen"},
            {"nome": "Abdominal supra", "grupo_muscular": "Abdômen"},

            {"nome": "Esteira", "grupo_muscular": "Cardio"},
            {"nome": "Bicicleta ergométrica", "grupo_muscular": "Cardio"},
            {"nome": "Elíptico", "grupo_muscular": "Cardio"},
            {"nome": "Escada", "grupo_muscular": "Cardio"},
        ]

        criados = 0

        for exercicio in exercicios:
            _, created = ExercicioBase.objects.get_or_create(
                nome=exercicio["nome"],
                defaults={"grupo_muscular": exercicio["grupo_muscular"]}
            )
            if created:
                criados += 1

        self.stdout.write(
            self.style.SUCCESS(f'{criados} exercícios cadastrados com sucesso!')
        )