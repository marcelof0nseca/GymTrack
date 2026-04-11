from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Meta, Treino, Exercicio, ExecucaoTreino, ExecucaoExercicio, ExercicioBase


class ConfirmarTreinoFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='123456')
        self.client.login(username='alice', password='123456')

        self.treino = Treino.objects.create(usuario=self.user, nome='Treino A')
        self.exercicio_1 = Exercicio.objects.create(treino=self.treino, nome='Supino', series=3, repeticoes=10)
        self.exercicio_2 = Exercicio.objects.create(treino=self.treino, nome='Rosca', series=3, repeticoes=12)

    def _criar_execucao(self):
        execucao = ExecucaoTreino.objects.create(treino=self.treino, status='em_andamento')
        item_1 = ExecucaoExercicio.objects.create(execucao=execucao, exercicio=self.exercicio_1)
        item_2 = ExecucaoExercicio.objects.create(execucao=execucao, exercicio=self.exercicio_2)
        return execucao, item_1, item_2

    def test_confirmar_treino_sem_exercicios_concluidos_mantem_em_andamento(self):
        execucao, _, _ = self._criar_execucao()

        resposta = self.client.post(
            reverse('confirmar_treino', args=[execucao.id]),
            {},
            follow=True
        )

        execucao.refresh_from_db()
        self.assertEqual(execucao.status, 'em_andamento')
        self.assertContains(resposta, 'Nenhum exercício foi concluído. O treino continua em andamento.')

    def test_confirmar_treino_parcial_sem_confirmacao_explicita_nao_conclui(self):
        execucao, item_1, _ = self._criar_execucao()
        item_1.concluido = True
        item_1.save(update_fields=['concluido'])

        resposta = self.client.post(
            reverse('confirmar_treino', args=[execucao.id]),
            {'confirm_partial': '0'},
            follow=True
        )

        execucao.refresh_from_db()
        self.assertEqual(execucao.status, 'em_andamento')
        self.assertContains(resposta, 'Ainda existem exercícios em andamento. Confirme para finalizar parcialmente.')

    def test_confirmar_treino_parcial_com_confirmacao_explicita_conclui(self):
        execucao, item_1, _ = self._criar_execucao()
        item_1.concluido = True
        item_1.save(update_fields=['concluido'])

        resposta = self.client.post(
            reverse('confirmar_treino', args=[execucao.id]),
            {'confirm_partial': '1'},
            follow=True
        )

        execucao.refresh_from_db()
        self.assertEqual(execucao.status, 'concluido')
        self.assertContains(resposta, 'Treino finalizado com exercícios pendentes.')

    def test_concluir_ultimo_exercicio_mantem_conclusao_automatica(self):
        execucao, item_1, item_2 = self._criar_execucao()

        self.client.post(reverse('concluir_exercicio', args=[item_1.id]), {}, follow=True)
        execucao.refresh_from_db()
        self.assertEqual(execucao.status, 'em_andamento')

        resposta = self.client.post(reverse('concluir_exercicio', args=[item_2.id]), {}, follow=True)
        execucao.refresh_from_db()
        self.assertEqual(execucao.status, 'concluido')
        self.assertContains(resposta, 'Treino concluído com sucesso!')

    def test_nao_permite_concluir_item_apos_treino_ser_finalizado_parcialmente(self):
        execucao, item_1, item_2 = self._criar_execucao()
        item_1.concluido = True
        item_1.save(update_fields=['concluido'])

        self.client.post(
            reverse('confirmar_treino', args=[execucao.id]),
            {'confirm_partial': '1'},
            follow=True
        )

        resposta = self.client.post(reverse('concluir_exercicio', args=[item_2.id]), {}, follow=True)

        execucao.refresh_from_db()
        item_2.refresh_from_db()
        self.assertEqual(execucao.status, 'concluido')
        self.assertFalse(item_2.concluido)
        self.assertContains(
            resposta,
            'Este treino já foi finalizado. Não é possível concluir exercícios pendentes depois do encerramento.'
        )

    def test_exibe_aviso_quando_treino_concluido_com_pendencias(self):
        execucao, item_1, _ = self._criar_execucao()
        item_1.concluido = True
        item_1.save(update_fields=['concluido'])

        self.client.post(
            reverse('confirmar_treino', args=[execucao.id]),
            {'confirm_partial': '1'},
            follow=True
        )

        resposta = self.client.get(reverse('execucao_detalhe', args=[execucao.id]))
        self.assertContains(resposta, 'Este treino foi concluído com 1 exercício(s) pendente(s).')

class FormSelectionUiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='bob', password='123456')
        self.client.login(username='bob', password='123456')

        self.treino = Treino.objects.create(usuario=self.user, nome='Treino B')
        self.exercicio_base = ExercicioBase.objects.create(
            nome='Supino inclinado',
            grupo_muscular='Peito'
        )

    def test_exercicios_page_exibe_hints_e_placeholders_de_selecao(self):
        resposta = self.client.get(reverse('exercicios'))

        self.assertContains(resposta, 'Selecione um treino')
        self.assertContains(resposta, 'Selecione um exerc')
        self.assertContains(resposta, 'Escolha um treino na lista. Esse campo')
        self.assertContains(resposta, 'Escolha um exerc')
        self.assertContains(resposta, 'aria-describedby="treino-select-hint"', html=False)
        self.assertContains(resposta, 'aria-describedby="exercicio-select-hint"', html=False)

    def test_execucao_page_exibe_hint_e_placeholder_de_selecao(self):
        resposta = self.client.get(reverse('execucao'))

        self.assertContains(resposta, 'Selecione um treino')
        self.assertContains(resposta, 'Escolha um treino na lista para iniciar. Esse campo')
        self.assertContains(resposta, 'aria-describedby="treino-select-hint"', html=False)

    def test_exercicios_post_impede_exercicio_duplicado_no_mesmo_treino(self):
        Exercicio.objects.create(
            treino=self.treino,
            exercicio_base=self.exercicio_base,
            series=4,
            repeticoes=10
        )

        resposta = self.client.post(reverse('exercicios'), {
            'treino': self.treino.id,
            'exercicio_base': self.exercicio_base.id,
            'series': 4,
            'repeticoes': 12,
        })

        self.assertEqual(
            Exercicio.objects.filter(
                treino=self.treino,
                exercicio_base=self.exercicio_base
            ).count(),
            1
        )
        self.assertContains(resposta, 'Esse exerc')

    def test_execucao_post_sem_exercicios_mantem_validacao(self):
        treino_sem_exercicios = Treino.objects.create(usuario=self.user, nome='Treino vazio')

        resposta = self.client.post(reverse('execucao'), {
            'treino': treino_sem_exercicios.id,
        })

        self.assertContains(
            resposta,
            'Esse treino ainda n'
        )


class MetasFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='carol', password='123456')
        self.client.login(username='carol', password='123456')

    def test_metas_get_exibe_formulario_e_lista_vazia(self):
        resposta = self.client.get(reverse('metas'))

        self.assertContains(resposta, 'Criar meta')
        self.assertContains(resposta, 'Nome da meta')
        self.assertContains(resposta, 'Nenhuma meta cadastrada até o momento.')

    def test_cria_meta_com_sucesso(self):
        prazo = timezone.localdate() + timedelta(days=7)

        resposta = self.client.post(reverse('metas'), {
            'nome': 'Perder 5 kg',
            'valor': '5.00',
            'prazo': prazo.isoformat(),
        }, follow=True)

        self.assertEqual(Meta.objects.filter(usuario=self.user).count(), 1)
        meta = Meta.objects.get(usuario=self.user)
        self.assertEqual(meta.nome, 'Perder 5 kg')
        self.assertEqual(str(meta.valor), '5.00')
        self.assertEqual(meta.prazo, prazo)
        self.assertContains(resposta, 'Meta criada com sucesso!')

    def test_rejeita_valor_zero_ou_negativo(self):
        prazo = timezone.localdate() + timedelta(days=7)

        resposta = self.client.post(reverse('metas'), {
            'nome': 'Meta inválida',
            'valor': '0',
            'prazo': prazo.isoformat(),
        })

        self.assertEqual(Meta.objects.filter(usuario=self.user).count(), 0)
        self.assertContains(resposta, 'O valor da meta deve ser maior que zero.')

    def test_rejeita_prazo_no_passado(self):
        prazo = timezone.localdate() - timedelta(days=1)

        resposta = self.client.post(reverse('metas'), {
            'nome': 'Meta atrasada',
            'valor': '10.00',
            'prazo': prazo.isoformat(),
        })

        self.assertEqual(Meta.objects.filter(usuario=self.user).count(), 0)
        self.assertContains(resposta, 'O prazo da meta não pode estar no passado.')

    def test_lista_apenas_metas_do_usuario_logado(self):
        outro_usuario = User.objects.create_user(username='dave', password='123456')
        prazo = timezone.localdate() + timedelta(days=3)

        Meta.objects.create(usuario=outro_usuario, nome='Meta de outro usuário', valor='8.00', prazo=prazo)
        Meta.objects.create(usuario=self.user, nome='Minha meta', valor='4.00', prazo=prazo)

        resposta = self.client.get(reverse('metas'))

        self.assertContains(resposta, 'Minha meta')
        self.assertNotContains(resposta, 'Meta de outro usuário')

    def test_exibe_tags_coloridas_para_status_da_meta(self):
        prazo_futuro = timezone.localdate() + timedelta(days=5)
        prazo_passado = timezone.localdate() - timedelta(days=2)

        Meta.objects.create(usuario=self.user, nome='Meta em andamento', valor='5.00', prazo=prazo_futuro)
        Meta.objects.create(usuario=self.user, nome='Meta concluída', valor='10.00', prazo=prazo_futuro, status='concluida')
        Meta.objects.create(usuario=self.user, nome='Meta vencida', valor='15.00', prazo=prazo_passado)

        resposta = self.client.get(reverse('metas'))

        self.assertContains(resposta, 'Em andamento')
        self.assertContains(resposta, 'Concluída')
        self.assertContains(resposta, 'Vencida')
        self.assertContains(resposta, 'meta-status--em-andamento', html=False)
        self.assertContains(resposta, 'meta-status--concluida', html=False)
        self.assertContains(resposta, 'meta-status--vencida', html=False)


class HomeMetasCardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='homeuser', password='123456')
        self.client.login(username='homeuser', password='123456')

    def test_home_exibe_metas_proximas_de_expirar_no_lugar_dos_exercicios(self):
        hoje = timezone.localdate()
        Meta.objects.create(
            usuario=self.user,
            nome='Meta próxima 1',
            valor='5.00',
            prazo=hoje + timedelta(days=2),
        )
        Meta.objects.create(
            usuario=self.user,
            nome='Meta próxima 2',
            valor='7.00',
            prazo=hoje + timedelta(days=1),
        )
        Meta.objects.create(
            usuario=self.user,
            nome='Meta distante',
            valor='10.00',
            prazo=hoje + timedelta(days=20),
        )

        resposta = self.client.get(reverse('home'))

        self.assertContains(resposta, 'Metas próximas de expirar')
        self.assertContains(resposta, 'Meta próxima 1')
        self.assertContains(resposta, 'Meta próxima 2')
        self.assertNotContains(resposta, 'Meta distante')
        self.assertNotContains(resposta, 'Exercícios adicionados')
        self.assertContains(resposta, 'Vence em 2 dias')
        self.assertContains(resposta, 'Vence amanhã')

    def test_home_mostra_metas_mais_proximas_quando_nao_ha_prazo_imediato(self):
        hoje = timezone.localdate()
        Meta.objects.create(
            usuario=self.user,
            nome='Meta distante 1',
            valor='5.00',
            prazo=hoje + timedelta(days=30),
        )
        Meta.objects.create(
            usuario=self.user,
            nome='Meta distante 2',
            valor='8.00',
            prazo=hoje + timedelta(days=15),
        )

        resposta = self.client.get(reverse('home'))

        self.assertContains(resposta, 'Metas próximas de expirar')
        self.assertContains(resposta, 'Meta distante 2')
        self.assertContains(resposta, 'Meta distante 1')
        self.assertContains(resposta, 'Vence em 15 dias')
        self.assertContains(resposta, 'Vence em 30 dias')
