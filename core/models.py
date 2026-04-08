from django.db import models
from django.contrib.auth.models import User


class Treino(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
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
    STATUS_CHOICES = [
        ('em_andamento', 'Em andamento'),
        ('concluido', 'Concluído'),
    ]

    treino = models.ForeignKey(Treino, on_delete=models.CASCADE, related_name='execucoes')
    data_execucao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_andamento')

    def __str__(self):
        return f"{self.treino.nome} - {self.get_status_display()}"

    @property
    def total_exercicios(self):
        return self.itens.count()

    @property
    def exercicios_concluidos(self):
        return self.itens.filter(concluido=True).count()

    @property
    def exercicios_pendentes(self):
        pendentes = self.total_exercicios - self.exercicios_concluidos
        return pendentes if pendentes > 0 else 0

    @property
    def tem_exercicios_concluidos(self):
        return self.exercicios_concluidos > 0

    @property
    def tem_exercicios_pendentes(self):
        return self.itens.filter(concluido=False).exists()

    @property
    def esta_parcial(self):
        return self.tem_exercicios_concluidos and self.tem_exercicios_pendentes

    @property
    def pode_concluir_automaticamente(self):
        return self.total_exercicios > 0 and not self.tem_exercicios_pendentes

    @property
    def concluido_com_pendencias(self):
        return self.status == 'concluido' and self.exercicios_pendentes > 0


class ExecucaoExercicio(models.Model):
    execucao = models.ForeignKey(ExecucaoTreino, on_delete=models.CASCADE, related_name='itens')
    exercicio = models.ForeignKey(Exercicio, on_delete=models.CASCADE)
    concluido = models.BooleanField(default=False)
    data_conclusao = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        nome_exercicio = self.exercicio.exercicio_base.nome if self.exercicio.exercicio_base else self.exercicio.nome
        return f"{nome_exercicio} - {self.execucao.treino.nome}"