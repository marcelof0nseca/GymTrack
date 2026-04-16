from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Treino(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)

    def __str__(self):
        return self.nome


class Meta(models.Model):
    STATUS_CHOICES = [
        ('em_andamento', 'Em andamento'),
        ('concluida', 'Concluída'),
        ('vencida', 'Vencida'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metas')
    nome = models.CharField(max_length=100)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    data_inicio = models.DateField(default=timezone.localdate)
    prazo = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='em_andamento')
    data_conclusao = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['prazo', 'id']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(valor__gt=0),
                name='meta_valor_positivo',
            ),
        ]

    def __str__(self):
        return f'{self.nome} - {self.usuario.username}'

    @property
    def status_visual(self):
        if self.status == 'concluida':
            return 'concluida'

        if self.prazo < timezone.localdate():
            return 'vencida'

        return 'em_andamento'

    @property
    def status_label(self):
        labels = dict(self.STATUS_CHOICES)
        return labels[self.status_visual]

    @property
    def status_css_slug(self):
        return {
            'em_andamento': 'em-andamento',
            'concluida': 'concluida',
            'vencida': 'vencida',
        }[self.status_visual]

    @property
    def dias_restantes(self):
        return (self.prazo - timezone.localdate()).days

    @property
    def prazo_resumo(self):
        dias = self.dias_restantes

        if dias < 0:
            dias_vencida = abs(dias)

            if dias_vencida == 1:
                return 'Vencida h\u00e1 1 dia'

            return f'Vencida h\u00e1 {dias_vencida} dias'

        if dias == 0:
            return 'Vence hoje'

        if dias == 1:
            return 'Vence amanhã'

        return f'Vence em {dias} dias'


class Atleta(models.Model):
    OBJETIVO_CHOICES = [
        ('emagrecimento', 'Emagrecimento'),
        ('ganho_massa', 'Ganho de massa'),
        ('reducao_cintura', 'Redução de cintura'),
    ]

    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='atleta')
    objetivo_principal = models.CharField(max_length=30, choices=OBJETIVO_CHOICES)
    objetivo_descricao = models.CharField(max_length=200, blank=True)
    altura_cm = models.DecimalField(max_digits=5, decimal_places=2)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(altura_cm__gt=0),
                name='atleta_altura_positiva',
            ),
        ]

    def __str__(self):
        return f'Atleta de {self.usuario.username}'

    @property
    def ultima_medicao(self):
        return self.medicoes.order_by('-data_registro', '-id').first()

    @property
    def total_medicoes(self):
        return self.medicoes.count()


class MedicaoAtleta(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='medicoes')
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2)
    braco_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    cintura_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    peito_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    coxa_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    data_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_registro', '-id']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(peso_kg__gt=0),
                name='medicao_peso_positivo',
            ),
            models.CheckConstraint(
                condition=models.Q(braco_cm__gt=0) | models.Q(braco_cm__isnull=True),
                name='medicao_braco_positivo_ou_nulo',
            ),
            models.CheckConstraint(
                condition=models.Q(cintura_cm__gt=0) | models.Q(cintura_cm__isnull=True),
                name='medicao_cintura_positiva_ou_nula',
            ),
            models.CheckConstraint(
                condition=models.Q(peito_cm__gt=0) | models.Q(peito_cm__isnull=True),
                name='medicao_peito_positivo_ou_nulo',
            ),
            models.CheckConstraint(
                condition=models.Q(coxa_cm__gt=0) | models.Q(coxa_cm__isnull=True),
                name='medicao_coxa_positiva_ou_nula',
            ),
        ]

    def __str__(self):
        return f'{self.atleta.usuario.username} - {self.data_registro:%d/%m/%Y %H:%M}'


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
