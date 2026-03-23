from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Treino, Exercicio, ExecucaoTreino, ExercicioBase


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='E-mail')
    username = forms.CharField(label='Nome de usuário')
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar senha', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class TreinoForm(forms.ModelForm):
    class Meta:
        model = Treino
        fields = ['nome']
        labels = {
            'nome': 'Nome do treino',
        }


class ExercicioForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = ['treino', 'exercicio_base', 'series', 'repeticoes']
        labels = {
            'treino': 'Treino',
            'exercicio_base': 'Exercício',
            'series': 'Séries',
            'repeticoes': 'Repetições',
        }


class ExecucaoTreinoForm(forms.ModelForm):
    class Meta:
        model = ExecucaoTreino
        fields = ['treino']
        labels = {
            'treino': 'Treino',
        }

    def clean_treino(self):
        treino = self.cleaned_data['treino']
        if treino.exercicios.count() == 0:
            raise forms.ValidationError('Não é possível registrar a execução de um treino sem exercícios.')
        return treino