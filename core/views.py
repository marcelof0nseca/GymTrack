from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import DatabaseError, transaction
from django.db.models.functions import Lower, Trim
from django.db.models import Case, When, Value, IntegerField
from datetime import timedelta
from django.urls import reverse
import logging

from .models import Atleta, MedicaoAtleta, Meta, Treino, Exercicio, ExecucaoTreino, ExecucaoExercicio
from .forms import (
    AtletaForm,
    ExercicioForm,
    ExecucaoTreinoForm,
    MedicaoAtletaForm,
    MetaForm,
    RegisterForm,
    TreinoForm,
)


logger = logging.getLogger(__name__)


def _concluir_execucao(execucao):
    if execucao.status != 'concluido':
        execucao.status = 'concluido'
        execucao.save(update_fields=['status'])


ATLETA_METRICAS = [
    ('peso_kg', 'Peso', 'kg'),
    ('braco_cm', 'Braço', 'cm'),
    ('cintura_cm', 'Cintura', 'cm'),
    ('peito_cm', 'Peito', 'cm'),
    ('coxa_cm', 'Coxa', 'cm'),
]


def _adicionar_erros_formulario(request, *forms):
    for form in forms:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)


def _listar_rotulos(rotulos):
    unicos = list(dict.fromkeys(rotulos))

    if not unicos:
        return ''

    if len(unicos) == 1:
        return unicos[0]

    return f"{', '.join(unicos[:-1])} e {unicos[-1]}"


def _avaliar_evolucao(atleta, medicao_anterior, nova_medicao):
    if not medicao_anterior:
        return False, []

    regras = {
        'emagrecimento': [
            ('peso_kg', 'down', 'Peso'),
            ('cintura_cm', 'down', 'Cintura'),
        ],
        'ganho_massa': [
            ('peso_kg', 'up', 'Peso'),
            ('braco_cm', 'up', 'Braço'),
            ('peito_cm', 'up', 'Peito'),
            ('coxa_cm', 'up', 'Coxa'),
        ],
        'reducao_cintura': [
            ('cintura_cm', 'down', 'Cintura'),
        ],
    }

    metricas_melhoradas = []

    for campo, direcao, rotulo in regras[atleta.objetivo_principal]:
        valor_anterior = getattr(medicao_anterior, campo)
        valor_novo = getattr(nova_medicao, campo)

        if valor_anterior is None or valor_novo is None:
            continue

        if direcao == 'down' and valor_novo < valor_anterior:
            metricas_melhoradas.append(rotulo)

        if direcao == 'up' and valor_novo > valor_anterior:
            metricas_melhoradas.append(rotulo)

    metricas_melhoradas = list(dict.fromkeys(metricas_melhoradas))
    return bool(metricas_melhoradas), metricas_melhoradas


def _mensagem_evolucao(atleta, metricas_melhoradas):
    medidas = _listar_rotulos(metricas_melhoradas)

    if atleta.objetivo_principal == 'ganho_massa':
        return f'Parabéns! Você evoluiu no objetivo de ganho de massa com avanço em {medidas}.'

    if atleta.objetivo_principal == 'reducao_cintura':
        return f'Parabéns! Você evoluiu no objetivo de redução de cintura com redução em {medidas}.'

    return f'Parabéns! Você evoluiu no objetivo de emagrecimento com redução em {medidas}.'


def _montar_metricas_medicao(medicao, medicao_anterior=None):
    if not medicao:
        return []

    metricas = []

    for campo, rotulo, unidade in ATLETA_METRICAS:
        valor = getattr(medicao, campo)
        if valor is None:
            continue

        item = {
            'campo': campo,
            'rotulo': rotulo,
            'unidade': unidade,
            'valor': valor,
        }

        if medicao_anterior:
            valor_anterior = getattr(medicao_anterior, campo)
            if valor_anterior is not None:
                delta = valor - valor_anterior
                if delta != 0:
                    item['delta'] = delta
                    item['delta_abs'] = abs(delta)
                    item['delta_direction'] = 'up' if delta > 0 else 'down'

        metricas.append(item)

    return metricas


def _montar_historico_medicoes(atleta):
    medicoes = list(atleta.medicoes.all())
    historico = []

    for indice, medicao in enumerate(medicoes):
        medicao_anterior = medicoes[indice + 1] if indice + 1 < len(medicoes) else None
        houve_evolucao, metricas_melhoradas = _avaliar_evolucao(atleta, medicao_anterior, medicao)

        historico.append({
            'medicao': medicao,
            'metricas': _montar_metricas_medicao(medicao, medicao_anterior),
            'medicao_anterior': medicao_anterior,
            'houve_evolucao': houve_evolucao,
            'metricas_melhoradas': metricas_melhoradas,
        })

    return historico


def _obter_atleta(usuario):
    return Atleta.objects.filter(usuario=usuario).prefetch_related('medicoes').first()


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
    atleta = _obter_atleta(request.user)
    medicao_atual_atleta = atleta.ultima_medicao if atleta else None
    hoje = timezone.localdate()
    limite_expiracao = hoje + timedelta(days=7)
    metas_proximas_expirar = Meta.objects.filter(
        usuario=request.user,
        prazo__gte=hoje,
        prazo__lte=limite_expiracao,
    ).exclude(
        status='concluida'
    ).order_by('prazo', 'id')[:3]

    if not metas_proximas_expirar:
        metas_proximas_expirar = Meta.objects.filter(
            usuario=request.user,
        ).exclude(
            status='concluida'
        ).order_by('prazo', 'id')[:3]

    return render(request, 'core/home.html', {
        'total_treinos': treinos.count(),
        'total_exercicios': exercicios.count(),
        'total_execucoes': execucoes.filter(status='concluido').count(),
        'ultimo_treino': treinos.first(),
        'ultima_execucao': execucoes.first(),
        'metas_proximas_expirar': metas_proximas_expirar,
        'atleta': atleta,
        'medicao_atual_atleta': medicao_atual_atleta,
    })


@login_required
def conta_view(request):
    atleta = _obter_atleta(request.user)

    return render(request, 'core/conta.html', {
        'atleta': atleta,
    })


@login_required
def perfil_view(request):
    return redirect('conta')


@login_required
def atleta_view(request):
    atleta = _obter_atleta(request.user)
    medicao_atual = atleta.ultima_medicao if atleta else None

    if not atleta:
        if request.method == 'POST':
            atleta_form = AtletaForm(request.POST)
            medicao_form = MedicaoAtletaForm(request.POST)

            if atleta_form.is_valid() and medicao_form.is_valid():
                with transaction.atomic():
                    atleta = atleta_form.save(commit=False)
                    atleta.usuario = request.user
                    atleta.save()

                    primeira_medicao = medicao_form.save(commit=False)
                    primeira_medicao.atleta = atleta
                    primeira_medicao.save()

                messages.success(
                    request,
                    'Perfil do atleta criado com sucesso! Agora você já pode acompanhar suas evoluções.'
                )
                return redirect('atleta')

            _adicionar_erros_formulario(request, atleta_form, medicao_form)
        else:
            atleta_form = AtletaForm()
            medicao_form = MedicaoAtletaForm()

        return render(request, 'core/atleta.html', {
            'atleta': None,
            'atleta_form': atleta_form,
            'medicao_form': medicao_form,
            'medicao_atual': None,
            'metricas_atuais': [],
            'historico_medicoes': [],
            'ultima_evolucao': False,
            'ultima_evolucao_resumo': '',
        })

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'dados_atleta':
            atleta_form = AtletaForm(request.POST, instance=atleta)
            medicao_form = MedicaoAtletaForm(medicao_referencia=medicao_atual)

            if atleta_form.is_valid():
                atleta_form.save()
                messages.success(request, 'Perfil do atleta atualizado com sucesso!')
                return redirect('atleta')

            _adicionar_erros_formulario(request, atleta_form)
        elif form_type == 'medidas_atleta':
            atleta_form = AtletaForm(instance=atleta)
            medicao_form = MedicaoAtletaForm(request.POST, medicao_referencia=medicao_atual)

            if medicao_form.is_valid():
                nova_medicao = medicao_form.save(commit=False)
                nova_medicao.atleta = atleta
                nova_medicao.save()

                houve_evolucao, metricas_melhoradas = _avaliar_evolucao(atleta, medicao_atual, nova_medicao)

                if houve_evolucao:
                    messages.success(request, _mensagem_evolucao(atleta, metricas_melhoradas))
                else:
                    messages.success(
                        request,
                        'Medidas atualizadas com sucesso! Continue acompanhando sua evolução.'
                    )

                return redirect('atleta')

            _adicionar_erros_formulario(request, medicao_form)
        else:
            return redirect('atleta')
    else:
        atleta_form = AtletaForm(instance=atleta)
        medicao_form = MedicaoAtletaForm(medicao_referencia=medicao_atual)

    medicao_atual = atleta.ultima_medicao
    historico_medicoes = _montar_historico_medicoes(atleta)
    ultima_evolucao = historico_medicoes[0]['houve_evolucao'] if historico_medicoes else False
    ultima_evolucao_resumo = _listar_rotulos(historico_medicoes[0]['metricas_melhoradas']) if ultima_evolucao else ''

    return render(request, 'core/atleta.html', {
        'atleta': atleta,
        'atleta_form': atleta_form,
        'medicao_form': medicao_form,
        'medicao_atual': medicao_atual,
        'metricas_atuais': _montar_metricas_medicao(medicao_atual),
        'historico_medicoes': historico_medicoes,
        'ultima_evolucao': ultima_evolucao,
        'ultima_evolucao_resumo': ultima_evolucao_resumo,
    })


@login_required
def metas_view(request):
    if request.method == 'POST':
        form = MetaForm(request.POST)

        if form.is_valid():
            try:
                meta = form.save(commit=False)
                meta.usuario = request.user
                meta.save()
            except DatabaseError:
                logger.exception('Erro ao salvar meta para o usuario %s', request.user.id)
                messages.error(
                    request,
                    'Nao foi possivel salvar a meta agora. Verifique se as migracoes do banco foram aplicadas no deploy.'
                )
            else:
                messages.success(request, 'Meta criada com sucesso!')
                return redirect('metas')

    else:
        form = MetaForm()

    hoje = timezone.localdate()

    try:
        metas = list(Meta.objects.filter(usuario=request.user).annotate(
            status_order=Case(
                When(status='concluida', then=Value(2)),
                When(prazo__lt=hoje, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('status_order', 'data_conclusao', 'prazo', 'id'))
    except DatabaseError:
        logger.exception('Erro ao carregar metas para o usuario %s', request.user.id)
        messages.error(
            request,
            'Nao foi possivel carregar as metas agora. Verifique se as migracoes do banco foram aplicadas no deploy.'
        )
        metas = []

    metas_em_andamento = sum(1 for meta in metas if meta.status_visual == 'em_andamento')
    metas_concluidas = sum(1 for meta in metas if meta.status_visual == 'concluida')
    metas_vencidas = sum(1 for meta in metas if meta.status_visual == 'vencida')
    proxima_meta = next((meta for meta in metas if meta.status_visual == 'em_andamento'), None)

    return render(request, 'core/metas.html', {
        'form': form,
        'metas': metas,
        'metas_em_andamento': metas_em_andamento,
        'metas_concluidas': metas_concluidas,
        'metas_vencidas': metas_vencidas,
        'proxima_meta': proxima_meta,
    })


@login_required
def confirmar_meta_view(request, meta_id):
    meta = get_object_or_404(Meta, id=meta_id, usuario=request.user)

    if request.method != 'POST':
        return redirect('metas')

    if meta.status == 'concluida':
        messages.info(request, 'Essa meta já está concluída.')
        return redirect('metas')

    if meta.status_visual == 'vencida':
        messages.error(request, 'Essa meta venceu e nao pode mais ser confirmada.')
        return redirect('metas')

    meta.status = 'concluida'
    meta.data_conclusao = timezone.now()
    meta.save(update_fields=['status', 'data_conclusao'])

    messages.success(request, 'Meta confirmada com sucesso!')
    return redirect(f"{reverse('metas')}?confirmada={meta.id}")


@login_required
def excluir_meta_view(request, meta_id):
    meta = get_object_or_404(Meta, id=meta_id, usuario=request.user)

    if request.method != 'POST':
        return redirect('metas')

    meta.delete()
    messages.success(request, 'Meta removida com sucesso!')
    return redirect('metas')


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
            _adicionar_erros_formulario(request, form)
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
