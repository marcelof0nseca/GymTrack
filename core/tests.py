from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Treino, Exercicio, ExecucaoTreino, ExecucaoExercicio


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
