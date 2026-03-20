from django.db import models



class Treino(models.Model):
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Exercicio(models.Model):
    treino = models.ForeignKey(Treino, on_delete=models.CASCADE, related_name='exercicios')
    nome = models.CharField(max_length=100)
    series = models.PositiveIntegerField()
    repeticoes = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.nome} - {self.treino.nome}"


class ExecucaoTreino(models.Model):
    treino = models.ForeignKey(Treino, on_delete=models.CASCADE, related_name='execucoes')
    data_execucao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.treino.nome} - {self.data_execucao.strftime('%d/%m/%Y %H:%M')}"
# Create your models here.
