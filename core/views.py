from django.shortcuts import render, redirect
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

    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    return render(request, 'core/home.html')


@login_required
def treinos_view(request):
    form = TreinoForm()

    if request.method == 'POST':
        form = TreinoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('treinos')

    treinos = Treino.objects.all()
    return render(request, 'core/treinos.html', {
        'form': form,
        'treinos': treinos
    })


@login_required
def exercicios_view(request):
    form = ExercicioForm()

    if request.method == 'POST':
        form = ExercicioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('exercicios')

    exercicios = Exercicio.objects.all()
    return render(request, 'core/exercicios.html', {
        'form': form,
        'exercicios': exercicios
    })


@login_required
def execucao_view(request):
    form = ExecucaoTreinoForm()

    if request.method == 'POST':
        form = ExecucaoTreinoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('execucao')

    execucoes = ExecucaoTreino.objects.all()
    return render(request, 'core/execucao.html', {
        'form': form,
        'execucoes': execucoes
    })