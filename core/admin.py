from django.contrib import admin
from .models import Meta, Treino, Exercicio, ExecucaoTreino, ExercicioBase

admin.site.register(Meta)
admin.site.register(Treino)
admin.site.register(ExercicioBase)
admin.site.register(Exercicio)
admin.site.register(ExecucaoTreino)