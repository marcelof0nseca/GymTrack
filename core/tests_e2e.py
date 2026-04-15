import os
import re
import unittest
from datetime import timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.test import tag
from django.utils import timezone

from .models import ExecucaoTreino, ExercicioBase, Meta, Treino

os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')

try:
    from playwright.sync_api import expect, sync_playwright
except ImportError:  # pragma: no cover - exercised in CI when dependency exists
    expect = None
    sync_playwright = None


@tag('e2e')
@unittest.skipUnless(sync_playwright, 'Playwright precisa estar instalado para executar os testes E2E.')
class GymTrackE2ETests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.artifacts_dir = Path(settings.BASE_DIR) / 'test-artifacts' / 'playwright'
        cls.artifacts_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.context = self.browser.new_context(record_video_dir=str(self.artifacts_dir))
        self.page = self.context.new_page()

    def tearDown(self):
        self.context.close()
        super().tearDown()

    def _url(self, path):
        return f'{self.live_server_url}{path}'

    def _registrar_usuario(self, username='e2e_user', email='e2e@example.com', password='SenhaForte123'):
        self.page.goto(self._url('/register/'))
        self.page.locator('[name="nome_completo"]').fill('Usuario E2E')
        self.page.locator('[name="username"]').fill(username)
        self.page.locator('[name="email"]').fill(email)
        self.page.locator('[name="password1"]').fill(password)
        self.page.locator('[name="password2"]').fill(password)
        self.page.locator('.auth-card form button[type="submit"]').click()

        expect(self.page).to_have_url(re.compile(rf'^{re.escape(self.live_server_url)}/$'))
        expect(self.page.locator('body')).to_contain_text('Sua conta')

    def test_fluxo_e2e_de_treino_do_cadastro_ate_a_execucao(self):
        exercicio_base = ExercicioBase.objects.create(nome='Supino reto', grupo_muscular='Peito')

        self._registrar_usuario()

        self.page.goto(self._url('/treinos/'))
        self.page.locator('[name="nome"]').fill('Treino E2E')
        self.page.locator('.content-card form button[type="submit"]').click()

        treino = Treino.objects.get(nome='Treino E2E')
        body = self.page.locator('body')
        expect(body).to_contain_text('Treino E2E')
        expect(body).to_contain_text('Treino criado com sucesso!')

        self.page.goto(self._url('/exercicios/'))
        self.page.locator('[name="treino"]').select_option(str(treino.id))
        self.page.locator('[name="exercicio_base"]').select_option(str(exercicio_base.id))
        self.page.locator('[name="series"]').fill('4')
        self.page.locator('[name="repeticoes"]').fill('10')
        self.page.locator('.content-card form button[type="submit"]').click()

        expect(body).to_contain_text('Supino reto')
        expect(body).to_contain_text('Treino E2E')

        self.page.goto(self._url('/execucao/'))
        self.page.locator('[name="treino"]').select_option(str(treino.id))
        self.page.locator('.content-card form button[type="submit"]').click()

        expect(self.page).to_have_url(re.compile(rf'^{re.escape(self.live_server_url)}/execucao/\d+/$'))
        execucao = ExecucaoTreino.objects.get(treino=treino)
        expect(body).to_contain_text('Supino reto')
        expect(self.page.locator('form[action*="/concluir/"] button[type="submit"]')).to_have_count(1)

        self.page.locator('form[action*="/concluir/"] button[type="submit"]').click()

        execucao.refresh_from_db()
        self.assertEqual(execucao.status, 'concluido')
        expect(body).to_contain_text('1/1')
        expect(self.page.locator('form[action*="/concluir/"] button[type="submit"]')).to_have_count(0)

    def test_fluxo_e2e_de_meta_com_confirmacao(self):
        hoje = timezone.localdate()
        prazo = hoje + timedelta(days=7)

        self._registrar_usuario(username='meta_user', email='meta@example.com')

        self.page.goto(self._url('/metas/'))
        self.page.locator('[name="nome"]').fill('Meta E2E')
        self.page.locator('[name="valor"]').fill('5.00')
        self.page.locator('[name="data_inicio"]').fill(hoje.isoformat())
        self.page.locator('[name="prazo"]').fill(prazo.isoformat())
        self.page.locator('.content-card form button[type="submit"]').click()

        body = self.page.locator('body')
        expect(body).to_contain_text('Meta criada com sucesso!')
        expect(body).to_contain_text('Meta E2E')
        expect(body).to_contain_text('Em andamento')

        meta = Meta.objects.get(nome='Meta E2E')
        self.page.locator('form[action*="/confirmar/"] button[type="submit"]').click()

        meta.refresh_from_db()
        self.assertEqual(meta.status, 'concluida')
        expect(body).to_contain_text('Meta confirmada com sucesso!')
        expect(self.page.locator('form[action*="/confirmar/"] button[type="submit"]')).to_have_count(0)
