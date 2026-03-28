from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Treino, Exercicio, ExecucaoTreino, ExercicioBase


class RegisterForm(UserCreationForm):
    nome_completo = forms.CharField(label='Nome completo', max_length=150)
    email = forms.EmailField(required=True, label='E-mail')
    username = forms.CharField(label='Nome de usuário')
    password1 = forms.CharField(label='Senha', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar senha', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['nome_completo', 'username', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)

        nome_completo = self.cleaned_data['nome_completo'].strip()
        partes_nome = nome_completo.split(' ', 1)

        user.first_name = partes_nome[0]
        user.last_name = partes_nome[1] if len(partes_nome) > 1 else ''
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user

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
            raise forms.ValidationError(
                'Esse treino ainda não possui exercícios cadastrados. Adicione pelo menos um exercício antes de finalizar.'
            )
        return treino