from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Treino, Exercicio, ExecucaoTreino


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class TreinoForm(forms.ModelForm):
    class Meta:
        model = Treino
        fields = ['nome']


class ExercicioForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = ['treino', 'nome', 'series', 'repeticoes']


class ExecucaoTreinoForm(forms.ModelForm):
    class Meta:
        model = ExecucaoTreino
        fields = ['treino']

    def clean_treino(self):
        treino = self.cleaned_data['treino']
        if treino.exercicios.count() == 0:
            raise forms.ValidationError('Não é possível registrar execução de um treino sem exercícios.')
        return treino