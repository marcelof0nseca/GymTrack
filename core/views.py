from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models.functions import Lower, Trim

from .models import Treino, Exercicio, ExecucaoTreino, ExecucaoExercicio, Meta
from .forms import RegisterForm, TreinoForm, ExercicioForm, ExecucaoTreinoForm, MetaForm


def _concluir_execucao(execucao):
    if execucao.status != 'concluido':
        execucao.status = 'concluido'
        execucao.save(update_fields=['status'])


def register_view(request):
    form = RegisterForm()

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Conta criada com sucesso! Bem-vindo ao GymTrack.')
            return redirect('home')

    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    form = AuthenticationForm()

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Login realizado com sucesso!')
            return redirect('home')

    form.fields['username'].label = 'Nome de usuário'
    form.fields['password'].label = 'Senha'

    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    treinos = Treino.objects.filter(usuario=request.user).order_by('-id')
    exercicios = Exercicio.objects.filter(treino__usuario=request.user)
    execucoes = ExecucaoTreino.objects.filter(
        treino__usuario=request.user
    ).select_related('treino').order_by('-id')

    return render(request, 'core/home.html', {
        'total_treinos': treinos.count(),
        'total_exercicios': exercicios.count(),
        'total_execucoes': execucoes.filter(status='concluido').count(),
        'ultimo_treino': treinos.first(),
        'ultima_execucao': execucoes.first(),
    })


@login_required
def perfil_view(request):
    return render(request, 'core/perfil.html')


@login_required
def metas_view(request):
    if request.method == 'POST':   #criacao
        form = MetaForm(request.POST)

        if form.is_valid():  #validacao
            meta = form.save(commit=False)
            meta.usuario = request.user
            meta.save()

            messages.success(request, 'Meta criada com sucesso!')
            return redirect('metas')
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
    else:
        form = MetaForm()

    metas = Meta.objects.filter(usuario=request.user).order_by('prazo')

    return render(request, 'core/metas.html', { #Redirecionamento para a mesma pagina
        'form': form,
        'metas': metas
    })


@login_required
def treinos_view(request):
    if request.method == 'POST':
        form = TreinoForm(request.POST)
        if form.is_valid():
            nome_treino = form.cleaned_data['nome'].strip()

            existe = Treino.objects.annotate(
                nome_limpo=Lower(Trim('nome'))
            ).filter(
                usuario=request.user,
                nome_limpo=nome_treino.lower()
            ).exists()

            if existe:
                messages.error(request, 'Você já possui um treino com esse nome.')
            else:
                treino = form.save(commit=False)
                treino.usuario = request.user
                treino.nome = nome_treino
                treino.save()
                messages.success(request, 'Treino criado com sucesso!')
                return redirect('treinos')
    else:
        form = TreinoForm()

    treinos = Treino.objects.filter(
        usuario=request.user
    ).prefetch_related('exercicios__exercicio_base').order_by('-id')

    return render(request, 'core/treinos.html', {
        'form': form,
        'treinos': treinos
    })


@login_required
def exercicios_view(request):
    if request.method == 'POST':
        form = ExercicioForm(request.POST)
        form.fields['treino'].queryset = Treino.objects.filter(usuario=request.user).order_by('-id')

        if form.is_valid():
            exercicio = form.save(commit=False)

            if exercicio.treino.usuario != request.user:
                messages.error(request, 'Você não tem permissão para adicionar exercícios a este treino.')
                return redirect('exercicios')

            exercicio.save()
            messages.success(request, 'Exercício adicionado com sucesso!')
            return redirect('exercicios')
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
    else:
        form = ExercicioForm()
        form.fields['treino'].queryset = Treino.objects.filter(usuario=request.user).order_by('-id')

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
        form.fields['treino'].queryset = Treino.objects.filter(usuario=request.user).order_by('-id')

        if form.is_valid():
            treino = form.cleaned_data['treino']

            if treino.usuario != request.user:
                messages.error(request, 'Você não tem permissão para iniciar este treino.')
                return redirect('execucao')

            execucao = ExecucaoTreino.objects.create(
                treino=treino,
                status='em_andamento'
            )

            for exercicio in treino.exercicios.all():
                ExecucaoExercicio.objects.create(
                    execucao=execucao,
                    exercicio=exercicio
                )

            messages.success(request, 'Treino iniciado com sucesso!')
            return redirect('execucao_detalhe', execucao_id=execucao.id)
        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(request, error)
    else:
        form = ExecucaoTreinoForm()
        form.fields['treino'].queryset = Treino.objects.filter(usuario=request.user).order_by('-id')

    execucoes = ExecucaoTreino.objects.select_related('treino').filter(
        treino__usuario=request.user
    ).order_by('-id')

    return render(request, 'core/execucao.html', {
        'form': form,
        'execucoes': execucoes
    })


@login_required
def execucao_detalhe_view(request, execucao_id):
    execucao = get_object_or_404(
        ExecucaoTreino.objects.select_related('treino').prefetch_related('itens__exercicio__exercicio_base'),
        id=execucao_id,
        treino__usuario=request.user
    )

    return render(request, 'core/execucao_detalhe.html', {
        'execucao': execucao
    })


@login_required
def concluir_exercicio_view(request, item_id):
    item = get_object_or_404(
        ExecucaoExercicio.objects.select_related('execucao', 'exercicio__exercicio_base'),
        id=item_id,
        execucao__treino__usuario=request.user
    )

    if request.method == 'POST':
        if item.execucao.status == 'concluido':
            messages.error(
                request,
                'Este treino já foi finalizado. Não é possível concluir exercícios pendentes depois do encerramento.'
            )
            return redirect('execucao_detalhe', execucao_id=item.execucao.id)

        if not item.concluido:
            item.concluido = True
            item.data_conclusao = timezone.now()
            item.save()

            execucao = item.execucao
            if execucao.pode_concluir_automaticamente:
                _concluir_execucao(execucao)
                messages.success(request, 'Treino concluído com sucesso!')
            else:
                messages.success(request, 'Exercício marcado como concluído!')

        return redirect('execucao_detalhe', execucao_id=item.execucao.id)

    return redirect('execucao')


@login_required
def confirmar_treino_view(request, execucao_id):
    execucao = get_object_or_404(
        ExecucaoTreino.objects.select_related('treino'),
        id=execucao_id,
        treino__usuario=request.user
    )

    if request.method != 'POST':
        return redirect('execucao_detalhe', execucao_id=execucao.id)

    if execucao.status == 'concluido':
        messages.error(request, 'Este treino já foi concluído.')
        return redirect('execucao_detalhe', execucao_id=execucao.id)

    if execucao.total_exercicios == 0 or not execucao.tem_exercicios_concluidos:
        messages.error(
            request,
            'Nenhum exercício foi concluído. O treino continua em andamento.'
        )
        return redirect('execucao_detalhe', execucao_id=execucao.id)

    confirm_partial = request.POST.get('confirm_partial') == '1'

    if execucao.esta_parcial and not confirm_partial:
        messages.error(
            request,
            'Ainda existem exercícios em andamento. Confirme para finalizar parcialmente.'
        )
        return redirect('execucao_detalhe', execucao_id=execucao.id)

    _concluir_execucao(execucao)

    if execucao.esta_parcial:
        messages.success(request, 'Treino finalizado com exercícios pendentes.')
    else:
        messages.success(request, 'Treino concluído com sucesso!')

    return redirect('execucao_detalhe', execucao_id=execucao.id)


@login_required
def excluir_treino(request, treino_id):
    treino = get_object_or_404(Treino, id=treino_id, usuario=request.user)

    if request.method == 'POST':
        treino.delete()
        messages.success(request, 'Treino excluído com sucesso!')
        return redirect('treinos')

    return redirect('treinos')


@login_required
def editar_treino_view(request, treino_id):
    treino = get_object_or_404(
        Treino.objects.prefetch_related('exercicios__exercicio_base'),
        id=treino_id,
        usuario=request.user
    )

    if request.method == 'POST':
        form = TreinoForm(request.POST, instance=treino)
        if form.is_valid():
            nome_treino = form.cleaned_data['nome'].strip()

            existe = Treino.objects.annotate(
                nome_limpo=Lower(Trim('nome'))
            ).filter(
                usuario=request.user,
                nome_limpo=nome_treino.lower()
            ).exclude(id=treino.id).exists()

            if existe:
                messages.error(request, 'Você já possui outro treino com esse nome.')
            else:
                treino_editado = form.save(commit=False)
                treino_editado.nome = nome_treino
                treino_editado.save()
                messages.success(request, 'Treino atualizado com sucesso!')
                return redirect('editar_treino', treino_id=treino.id)
    else:
        form = TreinoForm(instance=treino)

    return render(request, 'core/editar_treino.html', {
        'treino': treino,
        'form': form
    })


@login_required
def excluir_exercicio(request, exercicio_id):
    exercicio = get_object_or_404(
        Exercicio,
        id=exercicio_id,
        treino__usuario=request.user
    )

    if request.method == 'POST':
        treino_id = exercicio.treino.id
        exercicio.delete()
        messages.success(request, 'Exercício excluído com sucesso!')
        return redirect('editar_treino', treino_id=treino_id)

    return redirect('treinos')