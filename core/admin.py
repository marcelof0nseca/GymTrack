from django.contrib import admin
from .models import (
    Atleta,
    Exercicio,
    ExercicioBase,
    ExecucaoExercicio,
    ExecucaoTreino,
    MedicaoAtleta,
    Meta,
    Treino,
)


@admin.register(Meta)
class MetaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'usuario', 'valor', 'prazo', 'status')
    list_filter = ('status', 'prazo')
    search_fields = ('nome', 'usuario__username')


@admin.register(Treino)
class TreinoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'usuario')
    search_fields = ('nome', 'usuario__username')


@admin.register(ExercicioBase)
class ExercicioBaseAdmin(admin.ModelAdmin):
    list_display = ('nome', 'grupo_muscular')
    list_filter = ('grupo_muscular',)
    search_fields = ('nome', 'grupo_muscular')


@admin.register(Exercicio)
class ExercicioAdmin(admin.ModelAdmin):
    list_display = ('nome_exibicao', 'treino', 'series', 'repeticoes')
    search_fields = ('nome', 'exercicio_base__nome', 'treino__nome')

    @admin.display(description='Exercicio')
    def nome_exibicao(self, obj):
        return obj.exercicio_base.nome if obj.exercicio_base else obj.nome


@admin.register(ExecucaoTreino)
class ExecucaoTreinoAdmin(admin.ModelAdmin):
    list_display = ('treino', 'data_execucao', 'status')
    list_filter = ('status', 'data_execucao')
    search_fields = ('treino__nome', 'treino__usuario__username')


@admin.register(ExecucaoExercicio)
class ExecucaoExercicioAdmin(admin.ModelAdmin):
    list_display = ('execucao', 'exercicio', 'concluido', 'data_conclusao')
    list_filter = ('concluido', 'data_conclusao')
    search_fields = ('execucao__treino__nome', 'exercicio__nome', 'exercicio__exercicio_base__nome')


@admin.register(Atleta)
class AtletaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'objetivo_principal', 'altura_cm', 'atualizado_em')
    list_filter = ('objetivo_principal',)
    search_fields = ('usuario__username', 'objetivo_descricao')


@admin.register(MedicaoAtleta)
class MedicaoAtletaAdmin(admin.ModelAdmin):
    list_display = ('atleta', 'peso_kg', 'data_registro')
    list_filter = ('data_registro',)
    search_fields = ('atleta__usuario__username',)
