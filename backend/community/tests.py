from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from torcidas.models import Membro, Torcida
from .models import Publicacao, Notificacao

User = get_user_model()


class IsolamentoPublicacoesTests(APITestCase):
    def setUp(self):
        self.autor = User.objects.create_user(
            username="autor_teste", password="Senha-Forte-2026!"
        )
        self.estranho = User.objects.create_user(
            username="estranho_teste", password="Senha-Forte-2026!"
        )
        self.torcida = Torcida.objects.create(
            nome="Comunidade Teste", slug="comunidade-teste"
        )
        Membro.objects.create(
            usuario=self.autor, torcida=self.torcida, papel="admin"
        )
        self.publicacao = Publicacao.objects.create(
            torcida=self.torcida,
            autor=self.autor,
            texto="Publicação privada da torcida",
            status=Publicacao.Status.APROVADA,
        )

    def test_usuario_de_fora_nao_lista_publicacao(self):
        self.client.force_authenticate(user=self.estranho)
        response = self.client.get("/api/comunidade/publicacoes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_membro_consegue_listar_publicacao(self):
        self.client.force_authenticate(user=self.autor)
        response = self.client.get("/api/comunidade/publicacoes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_usuario_de_fora_nao_consegue_criar_publicacao_na_torcida(self):
        self.client.force_authenticate(user=self.estranho)
        response = self.client.post(
            "/api/comunidade/publicacoes/",
            {
                "torcida": self.torcida.pk,
                "texto": "Tentativa indevida",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            Publicacao.objects.filter(texto="Tentativa indevida").exists()
        )

from .models import Notificacao


class IsolamentoNotificacoesTests(APITestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(
            username="dono_notificacao", password="Senha-Forte-2026!"
        )
        self.outro = User.objects.create_user(
            username="outro_notificacao", password="Senha-Forte-2026!"
        )
        self.notificacao = Notificacao.objects.create(
            destinatario=self.usuario,
            ator=self.outro,
            tipo=Notificacao.Tipo.MENSAGEM,
            texto="Você recebeu uma nova mensagem.",
            referencia="conversa:123",
        )

    def test_usuario_lista_apenas_proprias_notificacoes(self):
        self.client.force_authenticate(user=self.outro)
        response = self.client.get("/api/comunidade/notificacoes/")
        self.assertEqual(response.status_code, 200)
        resultados = response.data.get("results", [])
        ids = [item["id"] for item in resultados]
        self.assertNotIn(self.notificacao.pk, ids)

    def test_usuario_nao_pode_marcar_notificacao_alheia_como_lida(self):
        self.client.force_authenticate(user=self.outro)
        response = self.client.post(
            f"/api/comunidade/notificacoes/{self.notificacao.pk}/ler/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
        self.notificacao.refresh_from_db()
        self.assertIsNone(self.notificacao.lida_em)

    def test_destinatario_pode_marcar_propria_notificacao_como_lida(self):
        self.client.force_authenticate(user=self.usuario)
        response = self.client.post(
            f"/api/comunidade/notificacoes/{self.notificacao.pk}/ler/",
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.notificacao.refresh_from_db()
        self.assertIsNotNone(self.notificacao.lida_em)

class PlatformAdminCommunityTests(APITestCase):
    def test_superuser_lista_publicacoes_de_outra_torcida(self):
        admin_global = User.objects.create_superuser(
            username="platform_admin_community", email="", password="Strong-Test-Password-2026!"
        )
        autor = User.objects.create_user(
            username="autor_global", password="Strong-Test-Password-2026!"
        )
        torcida = Torcida.objects.create(nome="Comunidade Global FC", slug="comunidade-global-fc")
        Membro.objects.create(usuario=autor, torcida=torcida, papel="admin")
        Publicacao.objects.create(torcida=torcida, autor=autor, texto="Post para moderação")
        self.client.force_authenticate(admin_global)
        response = self.client.get("/api/comunidade/publicacoes/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)


class AprovacaoObrigatoriaPublicacoesTests(APITestCase):
    def setUp(self):
        self.autor = User.objects.create_user(username="autor_pendente", password="Senha-Forte-2026!")
        self.admin_global = User.objects.create_superuser(username="admin_aprovador", email="", password="Senha-Forte-2026!")
        self.torcida = Torcida.objects.create(nome="Torcida Moderada", slug="torcida-moderada")
        Membro.objects.create(usuario=self.autor, torcida=self.torcida, papel="admin")
        self.client.force_authenticate(user=self.autor)

    def test_nova_publicacao_fica_pendente_e_nao_aparece_no_feed(self):
        response = self.client.post("/api/comunidade/publicacoes/", {"torcida": self.torcida.pk, "texto": "Aguardando análise"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], Publicacao.Status.PENDENTE)
        self.assertTrue(self.admin_global.notificacoes_torcida.filter(tipo=Notificacao.Tipo.PUBLICACAO_PENDENTE).exists())
        feed = self.client.get("/api/comunidade/publicacoes/")
        self.assertEqual(len(feed.data), 0)

    def test_apenas_admin_global_aprova_publicacao(self):
        post = Publicacao.objects.create(torcida=self.torcida, autor=self.autor, texto="Para aprovar")
        response = self.client.post(f"/api/comunidade/publicacoes/{post.pk}/aprovar/")
        self.assertEqual(response.status_code, 403)
        self.client.force_authenticate(user=self.admin_global)
        response = self.client.post(f"/api/comunidade/publicacoes/{post.pk}/aprovar/")
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.status, Publicacao.Status.APROVADA)

    def test_admin_global_pode_rejeitar_publicacao(self):
        post = Publicacao.objects.create(torcida=self.torcida, autor=self.autor, texto="Para rejeitar")
        self.client.force_authenticate(user=self.admin_global)
        response = self.client.post(f"/api/comunidade/publicacoes/{post.pk}/rejeitar/")
        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.status, Publicacao.Status.REJEITADA)
