from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Treino, Exercicio, ExecucaoTreino, ExercicioBase


def _append_widget_class(widget, class_name):
    current_class = widget.attrs.get('class', '').strip()
    widget.attrs['class'] = f'{current_class} {class_name}'.strip()


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

    def clean_nome(self):
        nome = self.cleaned_data['nome'].strip()
        return nome


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        treino_field = self.fields['treino']
        treino_field.empty_label = 'Selecione um treino'
        treino_field.queryset = treino_field.queryset.order_by('-id')
        _append_widget_class(treino_field.widget, 'form-select-input')
        treino_field.widget.attrs.update({
            'aria-describedby': 'treino-select-hint',
        })

        exercicio_field = self.fields['exercicio_base']
        exercicio_field.empty_label = 'Selecione um exercício'
        exercicio_field.queryset = ExercicioBase.objects.order_by('grupo_muscular', 'nome')
        _append_widget_class(exercicio_field.widget, 'form-select-input')
        exercicio_field.widget.attrs.update({
            'aria-describedby': 'exercicio-select-hint',
        })

        self.fields['series'].widget.attrs.update({
            'placeholder': 'Ex.: 4',
            'inputmode': 'numeric',
        })
        self.fields['repeticoes'].widget.attrs.update({
            'placeholder': 'Ex.: 12',
            'inputmode': 'numeric',
        })

    def clean(self):
        cleaned_data = super().clean()
        treino = cleaned_data.get('treino')
        exercicio_base = cleaned_data.get('exercicio_base')

        if treino and exercicio_base:
            qs = Exercicio.objects.filter(
                treino=treino,
                exercicio_base=exercicio_base
            )

            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    'Esse exercício já foi adicionado a este treino.'
                )

        return cleaned_data


class ExecucaoTreinoForm(forms.ModelForm):
    class Meta:
        model = ExecucaoTreino
        fields = ['treino']
        labels = {
            'treino': 'Treino',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        treino_field = self.fields['treino']
        treino_field.empty_label = 'Selecione um treino'
        treino_field.queryset = treino_field.queryset.order_by('-id')
        _append_widget_class(treino_field.widget, 'form-select-input')
        treino_field.widget.attrs.update({
            'aria-describedby': 'treino-select-hint',
        })

    def clean_treino(self):
        treino = self.cleaned_data['treino']
        if treino.exercicios.count() == 0:
            raise forms.ValidationError(
                'Esse treino ainda não possui exercícios cadastrados. Adicione pelo menos um exercício antes de iniciar.'
            )
        return treino
