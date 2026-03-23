from django.db import models


class Treino(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class ExercicioBase(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    grupo_muscular = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.nome} ({self.grupo_muscular})"

class Exercicio(models.Model):
    treino = models.ForeignKey(Treino, on_delete=models.CASCADE, related_name='exercicios')
    exercicio_base = models.ForeignKey(
        ExercicioBase,
        on_delete=models.CASCADE,
        related_name='exercicios_do_sistema',
        null=True,
        blank=True
    )
    nome = models.CharField(max_length=100, blank=True, null=True)
    series = models.PositiveIntegerField()
    repeticoes = models.PositiveIntegerField()

    def __str__(self):
        if self.exercicio_base:
            return f"{self.exercicio_base.nome} - {self.treino.nome}"
        return f"{self.nome} - {self.treino.nome}"


class ExecucaoTreino(models.Model):
    treino = models.ForeignKey(Treino, on_delete=models.CASCADE, related_name='execucoes')
    data_execucao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.treino.nome} - {self.data_execucao.strftime('%d/%m/%Y %H:%M')}"