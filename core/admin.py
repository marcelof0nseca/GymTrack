from django.contrib import admin
from .models import Atleta, Exercicio, ExercicioBase, ExecucaoTreino, MedicaoAtleta, Meta, Treino

admin.site.register(Meta)
admin.site.register(Treino)
admin.site.register(ExercicioBase)
admin.site.register(Exercicio)
admin.site.register(ExecucaoTreino)
admin.site.register(Atleta)
admin.site.register(MedicaoAtleta)
