from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

from .models import Treino, Exercicio, ExecucaoTreino
from .forms import RegisterForm, TreinoForm, ExercicioForm, ExecucaoTreinoForm
def register_view(request):
    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')

    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    form = AuthenticationForm()

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')

    form.fields['username'].label = 'Nome de usuário'
    form.fields['password'].label = 'Senha'

    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    treinos = Treino.objects.filter(usuario=request.user)
    exercicios = Exercicio.objects.filter(treino__usuario=request.user)
    execucoes = ExecucaoTreino.objects.filter(treino__usuario=request.user)

    return render(request, 'core/home.html', {
        'total_treinos': treinos.count(),
        'total_exercicios': exercicios.count(),
        'total_execucoes': execucoes.count()
    })

@login_required
def perfil_view(request):
    return render(request, 'core/perfil.html')


@login_required
def treinos_view(request):
    if request.method == 'POST':
        form = TreinoForm(request.POST)
        if form.is_valid():
            treino = form.save(commit=False)
            treino.usuario = request.user
            treino.save()
            return redirect('treinos')
    else:
        form = TreinoForm()

    treinos = Treino.objects.filter(
        usuario=request.user
    ).prefetch_related('exercicios__exercicio_base')

    return render(request, 'core/treinos.html', {
        'form': form,
        'treinos': treinos
    })


@login_required
def exercicios_view(request):
    if request.method == 'POST':
        form = ExercicioForm(request.POST)
        form.fields['treino'].queryset = Treino.objects.filter(usuario=request.user)

        if form.is_valid():
            exercicio = form.save(commit=False)

            if exercicio.treino.usuario != request.user:
                return redirect('exercicios')

            exercicio.save()
            return redirect('exercicios')
    else:
        form = ExercicioForm()
        form.fields['treino'].queryset = Treino.objects.filter(usuario=request.user)

    exercicios = Exercicio.objects.select_related(
        'treino',
        'exercicio_base'
    ).filter(
        treino__usuario=request.user
    ).order_by('exercicio_base__grupo_muscular', 'exercicio_base__nome')

    exercicios_agrupados = {}

    for exercicio in exercicios:
        grupo = exercicio.exercicio_base.grupo_muscular if exercicio.exercicio_base else 'Outros'

        if grupo not in exercicios_agrupados:
            exercicios_agrupados[grupo] = []

        exercicios_agrupados[grupo].append(exercicio)

    return render(request, 'core/exercicios.html', {
        'form': form,
        'exercicios_agrupados': exercicios_agrupados
    })

@login_required
def execucao_view(request):
    if request.method == 'POST':
        form = ExecucaoTreinoForm(request.POST)
        form.fields['treino'].queryset = Treino.objects.filter(usuario=request.user)

        if form.is_valid():
            execucao = form.save(commit=False)

            if execucao.treino.usuario != request.user:
                return redirect('execucao')

            execucao.save()
            return redirect('execucao')
    else:
        form = ExecucaoTreinoForm()
        form.fields['treino'].queryset = Treino.objects.filter(usuario=request.user)

    execucoes = ExecucaoTreino.objects.select_related('treino').filter(
        treino__usuario=request.user
    )

    return render(request, 'core/execucao.html', {
        'form': form,
        'execucoes': execucoes
    })


@login_required
def excluir_treino(request, treino_id):
    treino = get_object_or_404(Treino, id=treino_id, usuario=request.user)

    if request.method == 'POST':
        treino.delete()
        return redirect('treinos')

    return redirect('treinos')