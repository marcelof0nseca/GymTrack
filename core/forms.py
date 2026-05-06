from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import (
    Atleta,
    Exercicio,
    ExercicioBase,
    ExecucaoTreino,
    MedicaoAtleta,
    Meta,
    Treino,
)


def _append_widget_class(widget, class_name):
    current_class = widget.attrs.get('class', '').strip()
    widget.attrs['class'] = f'{current_class} {class_name}'.strip()


def _configure_decimal_field(field, placeholder):
    field.widget.attrs.update({
        'placeholder': placeholder,
        'step': '0.01',
        'min': '0.01',
        'inputmode': 'decimal',
    })


def _validate_positive_optional(form, field_name, label):
    value = form.cleaned_data.get(field_name)
    if value is not None and value <= 0:
        form.add_error(field_name, f'{label} deve ser maior que zero.')


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
        error_messages = {
            'nome': {
                'required': 'O nome do treino é obrigatório.',
            }
        }

    def clean_nome(self):
        nome = self.cleaned_data['nome'].strip()
        return nome


class AtletaForm(forms.ModelForm):
    class Meta:
        model = Atleta
        fields = ['objetivo_principal', 'objetivo_descricao', 'altura_cm']
        labels = {
            'objetivo_principal': 'Objetivo principal',
            'objetivo_descricao': 'Detalhes do objetivo',
            'altura_cm': 'Altura (cm)',
        }
        widgets = {
            'objetivo_descricao': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        objetivo_field = self.fields['objetivo_principal']
        objetivo_field.choices = [('', 'Selecione o objetivo principal'), *Atleta.OBJETIVO_CHOICES]
        _append_widget_class(objetivo_field.widget, 'form-select-input')
        objetivo_field.widget.attrs.update({
            'aria-describedby': 'objetivo-select-hint',
        })

        self.fields['objetivo_descricao'].widget.attrs.update({
            'placeholder': 'Ex.: reduzir gordura corporal e melhorar o condicionamento.',
        })
        _configure_decimal_field(self.fields['altura_cm'], 'Ex.: 175.00')

    def clean_altura_cm(self):
        altura_cm = self.cleaned_data['altura_cm']
        if altura_cm <= 0:
            raise forms.ValidationError('A altura deve ser maior que zero.')
        return altura_cm


class MedicaoAtletaForm(forms.ModelForm):
    class Meta:
        model = MedicaoAtleta
        fields = ['peso_kg', 'braco_cm', 'cintura_cm', 'peito_cm', 'coxa_cm']
        labels = {
            'peso_kg': 'Peso (kg)',
            'braco_cm': 'Braço (cm)',
            'cintura_cm': 'Cintura (cm)',
            'peito_cm': 'Peito (cm)',
            'coxa_cm': 'Coxa (cm)',
        }

    def __init__(self, *args, medicao_referencia=None, **kwargs):
        super().__init__(*args, **kwargs)

        if medicao_referencia and not self.is_bound:
            for field_name in self.fields:
                self.fields[field_name].initial = getattr(medicao_referencia, field_name)

        _configure_decimal_field(self.fields['peso_kg'], 'Ex.: 78.50')
        _configure_decimal_field(self.fields['braco_cm'], 'Ex.: 34.00')
        _configure_decimal_field(self.fields['cintura_cm'], 'Ex.: 82.00')
        _configure_decimal_field(self.fields['peito_cm'], 'Ex.: 98.00')
        _configure_decimal_field(self.fields['coxa_cm'], 'Ex.: 56.00')

        self.fields['peso_kg'].widget.attrs.update({
            'aria-describedby': 'medidas-atleta-hint',
        })

    def clean_peso_kg(self):
        peso_kg = self.cleaned_data['peso_kg']
        if peso_kg <= 0:
            raise forms.ValidationError('O peso deve ser maior que zero.')
        return peso_kg

    def clean(self):
        cleaned_data = super().clean()
        _validate_positive_optional(self, 'braco_cm', 'O braço')
        _validate_positive_optional(self, 'cintura_cm', 'A cintura')
        _validate_positive_optional(self, 'peito_cm', 'O peito')
        _validate_positive_optional(self, 'coxa_cm', 'A coxa')
        return cleaned_data


class MetaForm(forms.ModelForm):
    class Meta:
        model = Meta
        fields = ['nome', 'valor', 'data_inicio', 'prazo']
        labels = {
            'nome': 'Nome da meta',
            'valor': 'Valor',
            'data_inicio': 'Data inicial',
            'prazo': 'Data final',
        }
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'prazo': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        hoje = timezone.localdate().isoformat()

        self.fields['nome'].widget.attrs.update({
            'placeholder': 'Ex.: Perder 5 kg',
        })
        self.fields['valor'].widget.attrs.update({
            'placeholder': 'Ex.: 5.00',
            'step': '0.01',
            'min': '0.01',
            'inputmode': 'decimal',
        })
        self.fields['data_inicio'].widget.attrs.update({
            'min': hoje,
        })
        self.fields['prazo'].widget.attrs.update({
            'min': hoje,
        })

    def clean_nome(self):
        nome = self.cleaned_data['nome'].strip()
        if not nome:
            raise forms.ValidationError('O nome da meta não pode ser vazio.')
        return nome

    def clean_valor(self):
        valor = self.cleaned_data['valor']
        if valor <= 0:
            raise forms.ValidationError('O valor da meta deve ser maior que zero.')
        return valor

    def clean_data_inicio(self):
        data_inicio = self.cleaned_data['data_inicio']
        if data_inicio < timezone.localdate():
            raise forms.ValidationError('A data de início não pode estar no passado.')
        return data_inicio

    def clean_prazo(self):
        prazo = self.cleaned_data['prazo']
        if prazo < timezone.localdate():
            raise forms.ValidationError('O prazo da meta não pode estar no passado.')
        return prazo

    def clean(self):
        cleaned_data = super().clean()
        data_inicio = cleaned_data.get('data_inicio')
        prazo = cleaned_data.get('prazo')

        if data_inicio and prazo and prazo <= data_inicio:
            self.add_error('prazo', 'A data de término não pode ser anterior à data de início.')

        return cleaned_data


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


class RelatorioMensalTreinosForm(forms.Form):
    mes = forms.CharField(
        label='Mês',
        widget=forms.TextInput(attrs={'type': 'month'}),
    )
    treino = forms.ModelChoiceField(
        label='Treino',
        queryset=Treino.objects.none(),
        required=False,
        empty_label='Todos os treinos',
    )
    status = forms.ChoiceField(
        label='Status',
        required=False,
        choices=[
            ('', 'Todos os status'),
            *ExecucaoTreino.STATUS_CHOICES,
        ],
    )

    def __init__(self, *args, usuario=None, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_bound:
            hoje = timezone.localdate()
            self.fields['mes'].initial = hoje.strftime('%Y-%m')

        self.fields['mes'].widget.attrs.update({
            'aria-describedby': 'mes-relatorio-hint',
        })

        treino_field = self.fields['treino']
        treino_field.queryset = Treino.objects.filter(usuario=usuario).order_by('nome') if usuario else Treino.objects.none()
        _append_widget_class(treino_field.widget, 'form-select-input')

        status_field = self.fields['status']
        _append_widget_class(status_field.widget, 'form-select-input')

    def clean_mes(self):
        mes = self.cleaned_data['mes']

        try:
            ano, numero_mes = [int(parte) for parte in mes.split('-', 1)]
            return date(ano, numero_mes, 1)
        except (TypeError, ValueError):
            raise forms.ValidationError('Informe um mês válido.')
