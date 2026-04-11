from django.contrib import admin
from .models import Treino, Exercicio, ExecucaoTreino, ExercicioBase, Meta

admin.site.register(Treino)
admin.site.register(ExercicioBase)
admin.site.register(Exercicio)
admin.site.register(ExecucaoTreino)
admin.site.register(Meta)


