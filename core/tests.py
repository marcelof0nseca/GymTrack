from datetime import timedelta

from django.contrib.auth.models import User
from django.db import DatabaseError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from unittest.mock import patch

from .models import Atleta, Exercicio, ExercicioBase, ExecucaoExercicio, ExecucaoTreino, MedicaoAtleta, Meta, Treino


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
        self.assertContains(resposta, 'Data inicial')
        self.assertContains(resposta, 'Data final')
        self.assertContains(resposta, 'Nenhuma meta cadastrada até o momento.')

    def test_cria_meta_com_sucesso(self):
        data_inicio = timezone.localdate()
        prazo = timezone.localdate() + timedelta(days=7)

        resposta = self.client.post(reverse('metas'), {
            'nome': 'Perder 5 kg',
            'valor': '5.00',
            'data_inicio': data_inicio.isoformat(),
            'prazo': prazo.isoformat(),
        }, follow=True)

        self.assertEqual(Meta.objects.filter(usuario=self.user).count(), 1)
        meta = Meta.objects.get(usuario=self.user)
        self.assertEqual(meta.nome, 'Perder 5 kg')
        self.assertEqual(str(meta.valor), '5.00')
        self.assertEqual(meta.data_inicio, data_inicio)
        self.assertEqual(meta.prazo, prazo)
        self.assertContains(resposta, 'Meta criada com sucesso!')

    def test_criar_meta_trata_falha_de_banco_sem_500(self):
        data_inicio = timezone.localdate()
        prazo = timezone.localdate() + timedelta(days=7)

        with patch('core.views.Meta.save', side_effect=DatabaseError('falha simulada')):
            resposta = self.client.post(reverse('metas'), {
                'nome': 'Perder 5 kg',
                'valor': '5.00',
                'data_inicio': data_inicio.isoformat(),
                'prazo': prazo.isoformat(),
            })

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(
            resposta,
            'Nao foi possivel salvar a meta agora. Verifique se as migracoes do banco foram aplicadas no deploy.'
        )
        self.assertEqual(Meta.objects.filter(usuario=self.user).count(), 0)

    def test_rejeita_valor_zero_ou_negativo(self):
        data_inicio = timezone.localdate()
        prazo = timezone.localdate() + timedelta(days=7)

        resposta = self.client.post(reverse('metas'), {
            'nome': 'Meta inválida',
            'valor': '0',
            'data_inicio': data_inicio.isoformat(),
            'prazo': prazo.isoformat(),
        })

        self.assertEqual(Meta.objects.filter(usuario=self.user).count(), 0)
        self.assertContains(resposta, 'O valor da meta deve ser maior que zero.')

    def test_rejeita_prazo_no_passado(self):
        data_inicio = timezone.localdate()
        prazo = timezone.localdate() - timedelta(days=1)

        resposta = self.client.post(reverse('metas'), {
            'nome': 'Meta atrasada',
            'valor': '10.00',
            'data_inicio': data_inicio.isoformat(),
            'prazo': prazo.isoformat(),
        })

        self.assertEqual(Meta.objects.filter(usuario=self.user).count(), 0)
        self.assertContains(resposta, 'O prazo da meta não pode estar no passado.')

    def test_rejeita_data_final_igual_a_data_inicial(self):
        data_inicio = timezone.localdate() + timedelta(days=10)
        prazo = data_inicio

        resposta = self.client.post(reverse('metas'), {
            'nome': 'Meta com datas invalidas',
            'valor': '10.00',
            'data_inicio': data_inicio.isoformat(),
            'prazo': prazo.isoformat(),
        })

        self.assertEqual(Meta.objects.filter(usuario=self.user).count(), 0)
        self.assertContains(resposta, 'A data de término não pode ser anterior à data de início.')

    def test_lista_apenas_metas_do_usuario_logado(self):
        outro_usuario = User.objects.create_user(username='dave', password='123456')
        prazo = timezone.localdate() + timedelta(days=3)

        Meta.objects.create(usuario=outro_usuario, nome='Meta de outro usuário', valor='8.00', prazo=prazo)
        Meta.objects.create(usuario=self.user, nome='Minha meta', valor='4.00', prazo=prazo)

        resposta = self.client.get(reverse('metas'))

        self.assertContains(resposta, 'Minha meta')
        self.assertNotContains(resposta, 'Meta de outro usuário')

    def test_metas_get_trata_falha_de_banco_sem_500(self):
        with patch('core.views.Meta.objects.filter', side_effect=DatabaseError('falha simulada')):
            resposta = self.client.get(reverse('metas'))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(
            resposta,
            'Nao foi possivel carregar as metas agora. Verifique se as migracoes do banco foram aplicadas no deploy.'
        )

    def test_confirma_meta_e_exibe_tag_concluida_animada(self):
        prazo = timezone.localdate() + timedelta(days=4)
        meta = Meta.objects.create(usuario=self.user, nome='Meta para confirmar', valor='12.00', prazo=prazo)

        resposta = self.client.post(reverse('confirmar_meta', args=[meta.id]), {}, follow=True)

        meta.refresh_from_db()
        self.assertEqual(meta.status, 'concluida')
        self.assertIsNotNone(meta.data_conclusao)
        self.assertContains(resposta, 'Meta confirmada com sucesso!')
        self.assertContains(resposta, 'meta-status--concluida', html=False)
        self.assertContains(resposta, 'meta-status--confirmed', html=False)
        self.assertNotContains(resposta, 'Confirmar meta')

    def test_remove_meta_com_o_x_do_card(self):
        prazo = timezone.localdate() + timedelta(days=6)
        meta = Meta.objects.create(usuario=self.user, nome='Meta para remover', valor='8.00', prazo=prazo)

        resposta_inicial = self.client.get(reverse('metas'))
        self.assertContains(resposta_inicial, 'Tem certeza que deseja remover esta meta?')
        self.assertContains(resposta_inicial, 'Remoção de meta')
        self.assertContains(resposta_inicial, 'aria-label="Remover meta"', html=False)

        resposta = self.client.post(reverse('excluir_meta', args=[meta.id]), {}, follow=True)

        self.assertEqual(Meta.objects.filter(id=meta.id).count(), 0)
        self.assertContains(resposta, 'Meta removida com sucesso!')
        self.assertNotContains(resposta, 'Meta para remover')

    def test_metas_confirmadas_vao_para_o_final_da_pilha(self):
        hoje = timezone.localdate()
        meta_antiga = Meta.objects.create(
            usuario=self.user,
            nome='Meta antiga concluída',
            valor='5.00',
            prazo=hoje + timedelta(days=8),
            status='concluida',
            data_conclusao=timezone.now() - timedelta(days=2),
        )
        meta_nova = Meta.objects.create(
            usuario=self.user,
            nome='Meta nova concluída',
            valor='7.00',
            prazo=hoje + timedelta(days=8),
            status='concluida',
            data_conclusao=timezone.now() - timedelta(hours=1),
        )
        meta_pendente = Meta.objects.create(
            usuario=self.user,
            nome='Meta pendente',
            valor='9.00',
            prazo=hoje + timedelta(days=1),
        )

        resposta = self.client.get(reverse('metas'))

        pos_pendente = resposta.content.decode().find(meta_pendente.nome)
        pos_antiga = resposta.content.decode().find(meta_antiga.nome)
        pos_nova = resposta.content.decode().find(meta_nova.nome)

        self.assertGreater(pos_antiga, pos_pendente)
        self.assertGreater(pos_nova, pos_antiga)
        self.assertContains(resposta, 'Confirmar meta')

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

        self.assertContains(resposta, 'Metas próximas')
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

        self.assertContains(resposta, 'Metas próximas')
        self.assertContains(resposta, 'Meta distante 2')
        self.assertContains(resposta, 'Meta distante 1')
        self.assertContains(resposta, 'Vence em 15 dias')
        self.assertContains(resposta, 'Vence em 30 dias')


class PerfilAtletaFeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='athleteuser', password='123456')
        self.client.login(username='athleteuser', password='123456')

    def _criar_atleta_com_medicao(self, objetivo='emagrecimento', peso='90.00', cintura='100.00'):
        atleta = Atleta.objects.create(
            usuario=self.user,
            objetivo_principal=objetivo,
            objetivo_descricao='Quero acompanhar minha evolução física.',
            altura_cm='175.00',
        )
        medicao = MedicaoAtleta.objects.create(
            atleta=atleta,
            peso_kg=peso,
            braco_cm='34.00',
            cintura_cm=cintura,
            peito_cm='98.00',
            coxa_cm='58.00',
        )
        return atleta, medicao

    def test_atleta_get_sem_perfil_exibe_formulario_de_criacao(self):
        resposta = self.client.get(reverse('atleta'))

        self.assertContains(resposta, 'Criar perfil do atleta')
        self.assertContains(resposta, 'Objetivo principal')
        self.assertContains(resposta, 'Peso inicial (kg)')

    def test_atleta_post_cria_perfil_com_sucesso(self):
        resposta = self.client.post(reverse('atleta'), {
            'objetivo_principal': 'emagrecimento',
            'objetivo_descricao': 'Perder gordura e melhorar o condicionamento.',
            'altura_cm': '172.00',
            'peso_kg': '84.50',
            'braco_cm': '33.00',
            'cintura_cm': '88.00',
            'peito_cm': '97.00',
            'coxa_cm': '57.00',
        }, follow=True)

        self.assertEqual(Atleta.objects.filter(usuario=self.user).count(), 1)
        atleta = Atleta.objects.get(usuario=self.user)
        self.assertEqual(MedicaoAtleta.objects.filter(atleta=atleta).count(), 1)
        self.assertContains(resposta, 'Perfil do atleta criado com sucesso!')
        self.assertContains(resposta, 'Emagrecimento')
        self.assertContains(resposta, '84,50 kg')

    def test_atleta_post_rejeita_campos_obrigatorios_ausentes(self):
        resposta = self.client.post(reverse('atleta'), {
            'objetivo_principal': '',
            'objetivo_descricao': '',
            'altura_cm': '',
            'peso_kg': '',
        })

        self.assertEqual(Atleta.objects.filter(usuario=self.user).count(), 0)
        self.assertContains(resposta, 'Este campo é obrigatório.')

    def test_atleta_post_rejeita_dados_invalidos(self):
        resposta = self.client.post(reverse('atleta'), {
            'objetivo_principal': 'ganho_massa',
            'objetivo_descricao': 'Ganhar massa muscular.',
            'altura_cm': '-170.00',
            'peso_kg': '-82.00',
            'braco_cm': '-33.00',
            'cintura_cm': '0',
            'peito_cm': '95.00',
            'coxa_cm': '55.00',
        })

        self.assertEqual(Atleta.objects.filter(usuario=self.user).count(), 0)
        self.assertContains(resposta, 'A altura deve ser maior que zero.')
        self.assertContains(resposta, 'O peso deve ser maior que zero.')
        self.assertContains(resposta, 'O braço deve ser maior que zero.')
        self.assertContains(resposta, 'A cintura deve ser maior que zero.')

    def test_atleta_post_cria_nova_medicao_sem_apagar_historico(self):
        atleta, _ = self._criar_atleta_com_medicao()

        resposta = self.client.post(reverse('atleta'), {
            'form_type': 'medidas_atleta',
            'peso_kg': '88.00',
            'braco_cm': '34.50',
            'cintura_cm': '96.00',
            'peito_cm': '98.50',
            'coxa_cm': '58.50',
        }, follow=True)

        self.assertEqual(MedicaoAtleta.objects.filter(atleta=atleta).count(), 2)
        self.assertContains(resposta, 'Histórico de medições')
        self.assertContains(resposta, '88,00 kg')

    def test_atleta_post_exibe_mensagem_de_parabens_quando_ha_evolucao(self):
        atleta, _ = self._criar_atleta_com_medicao(objetivo='emagrecimento', peso='90.00', cintura='100.00')

        resposta = self.client.post(reverse('atleta'), {
            'form_type': 'medidas_atleta',
            'peso_kg': '87.50',
            'braco_cm': '34.00',
            'cintura_cm': '96.00',
            'peito_cm': '98.00',
            'coxa_cm': '58.00',
        }, follow=True)

        self.assertEqual(MedicaoAtleta.objects.filter(atleta=atleta).count(), 2)
        self.assertContains(resposta, 'Parabéns!')
        self.assertContains(resposta, 'redução em Peso e Cintura')

    def test_atleta_post_exibe_mensagem_neutra_quando_nao_ha_evolucao(self):
        atleta, _ = self._criar_atleta_com_medicao(objetivo='emagrecimento', peso='90.00', cintura='100.00')

        resposta = self.client.post(reverse('atleta'), {
            'form_type': 'medidas_atleta',
            'peso_kg': '91.00',
            'braco_cm': '34.00',
            'cintura_cm': '101.00',
            'peito_cm': '98.00',
            'coxa_cm': '58.00',
        }, follow=True)

        self.assertEqual(MedicaoAtleta.objects.filter(atleta=atleta).count(), 2)
        self.assertContains(resposta, 'Medidas atualizadas com sucesso! Continue acompanhando sua evolução.')

    def test_atleta_alias_perfil_redireciona_para_conta(self):
        resposta = self.client.get(reverse('perfil'))

        self.assertRedirects(resposta, reverse('conta'))


class ContaENavegacaoTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='navuser', password='123456', email='nav@example.com')
        self.client.login(username='navuser', password='123456')

    def test_home_exibe_cta_para_criar_perfil_do_atleta_quando_nao_existe(self):
        resposta = self.client.get(reverse('home'))

        self.assertContains(resposta, 'Criar perfil do atleta')
        self.assertContains(resposta, 'Sua conta')

    def test_home_exibe_resumo_do_atleta_quando_perfil_existe(self):
        atleta = Atleta.objects.create(
            usuario=self.user,
            objetivo_principal='ganho_massa',
            objetivo_descricao='Ganhar massa muscular com consistência.',
            altura_cm='180.00',
        )
        MedicaoAtleta.objects.create(
            atleta=atleta,
            peso_kg='79.50',
            braco_cm='35.00',
            cintura_cm='84.00',
            peito_cm='101.00',
            coxa_cm='59.00',
        )

        resposta = self.client.get(reverse('home'))

        self.assertContains(resposta, 'Perfil do atleta')
        self.assertContains(resposta, 'Ganho de massa')
        self.assertContains(resposta, 'Ver perfil do atleta')

    def test_base_nav_exibe_conta_e_perfil_do_atleta(self):
        resposta = self.client.get(reverse('home'))

        self.assertContains(resposta, 'Conta')
        self.assertContains(resposta, 'Perfil do Atleta')

    def test_conta_exibe_dados_da_conta_e_atalho_do_atleta(self):
        resposta = self.client.get(reverse('conta'))

        self.assertContains(resposta, 'Minha conta')
        self.assertContains(resposta, self.user.username)
        self.assertContains(resposta, 'Criar perfil do atleta')
