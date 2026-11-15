from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from torcidas.models import Membro, Torcida
from .models import Conversa, Mensagem

User = get_user_model()


class ChatApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(username="chat_admin", password="Senha-Forte-2026!")
        self.outro = User.objects.create_user(username="chat_outro", password="Senha-Forte-2026!")
        self.estranho = User.objects.create_user(username="chat_estranho", password="Senha-Forte-2026!")
        self.torcida = Torcida.objects.create(nome="Chat Teste", slug="chat-teste")
        Membro.objects.create(usuario=self.admin, torcida=self.torcida, papel="admin")
        Membro.objects.create(usuario=self.outro, torcida=self.torcida, papel="membro")

    def criar_conversa(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/chat/conversas/", {
            "torcida": self.torcida.pk,
            "tipo": "privada",
            "participantes": [self.outro.pk],
        }, format="json")
        self.assertEqual(response.status_code, 201)
        return response.data["id"]

    def test_cria_conversa_e_envia_mensagem(self):
        conversa_id = self.criar_conversa()
        response = self.client.post(f"/api/chat/conversas/{conversa_id}/mensagens/", {
            "conteudo": "Vamos ao jogo!"
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["conteudo"], "Vamos ao jogo!")
        from community.models import Notificacao
        self.assertEqual(
            Notificacao.objects.filter(
                destinatario=self.outro,
                ator=self.admin,
                tipo=Notificacao.Tipo.MENSAGEM,
                referencia=f"conversa:{conversa_id}",
            ).count(),
            1,
        )
        self.assertFalse(
            Notificacao.objects.filter(
                destinatario=self.admin,
                tipo=Notificacao.Tipo.MENSAGEM,
            ).exists()
        )

    def test_notificacoes_nao_sao_visiveis_para_outro_usuario(self):
        from community.models import Notificacao
        conversa_id = self.criar_conversa()
        self.client.post(
            f"/api/chat/conversas/{conversa_id}/mensagens/",
            {"conteudo": "Mensagem privada"},
            format="json",
        )
        self.client.force_authenticate(self.estranho)
        response = self.client.get("/api/comunidade/notificacoes/")
        self.assertEqual(response.status_code, 200)
        results = response.data.get("results", [])
        self.assertFalse(
            any(item.get("tipo") == Notificacao.Tipo.MENSAGEM for item in results)
        )

    def test_usuario_de_fora_nao_acessa_conversa(self):
        conversa_id = self.criar_conversa()
        self.client.force_authenticate(self.estranho)
        response = self.client.get(f"/api/chat/conversas/{conversa_id}/mensagens/")
        self.assertEqual(response.status_code, 404)

    def test_nao_cria_conversa_com_nao_membro(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/chat/conversas/", {
            "torcida": self.torcida.pk,
            "tipo": "privada",
            "participantes": [self.estranho.pk],
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Conversa.objects.count(), 0)

class PlatformAdminChatAccessTests(APITestCase):
    def setUp(self):
        self.platform_admin = User.objects.create_superuser(
            username="platform_chat_admin", email="", password="Strong-Test-Password-2026!"
        )
        self.member = User.objects.create_user(
            username="platform_chat_member", password="Strong-Test-Password-2026!"
        )
        self.torcida = Torcida.objects.create(nome="Chat Global FC", slug="chat-global-fc")
        Membro.objects.create(usuario=self.member, torcida=self.torcida, papel="admin")
        self.conversa = Conversa.objects.create(
            torcida=self.torcida, tipo=Conversa.Tipo.GRUPO,
            nome="Grupo de teste", criada_por=self.member,
        )
        from .models import ParticipanteConversa
        ParticipanteConversa.objects.create(conversa=self.conversa, usuario=self.member)
        Mensagem.objects.create(
            conversa=self.conversa, autor=self.member, conteudo="Mensagem para moderação"
        )

    def test_superuser_lista_conversas_e_consulta_mensagens(self):
        self.client.force_authenticate(self.platform_admin)
        lista = self.client.get("/api/chat/conversas/")
        self.assertEqual(lista.status_code, 200)
        self.assertEqual(len(lista.data), 1)
        mensagens = self.client.get(f"/api/chat/conversas/{self.conversa.pk}/mensagens/")
        self.assertEqual(mensagens.status_code, 200)
        self.assertEqual(len(mensagens.data), 1)
        self.assertEqual(mensagens.data[0]["conteudo"], "Mensagem para moderação")


class PelotaoChatScopeTests(APITestCase):
    def setUp(self):
        from torcidas.models import Pelotao
        self.admin = User.objects.create_user(username="pelotao_chat_admin", password="Senha-Forte-2026!")
        self.integrante = User.objects.create_user(username="pelotao_chat_member", password="Senha-Forte-2026!")
        self.segundo = User.objects.create_user(username="pelotao_chat_member2", password="Senha-Forte-2026!")
        self.fora = User.objects.create_user(username="pelotao_chat_outside", password="Senha-Forte-2026!")
        self.torcida = Torcida.objects.create(nome="Torcida Pelotão Chat", slug="torcida-pelotao-chat")
        self.pelotao = Pelotao.objects.create(torcida=self.torcida, nome="Norte", slug="norte")
        Membro.objects.create(usuario=self.admin, torcida=self.torcida, papel="admin", pelotao=self.pelotao)
        Membro.objects.create(usuario=self.integrante, torcida=self.torcida, pelotao=self.pelotao)
        Membro.objects.create(usuario=self.segundo, torcida=self.torcida, pelotao=self.pelotao)
        Membro.objects.create(usuario=self.fora, torcida=self.torcida, papel="membro")

    def test_integrante_cria_conversa_restrita_ao_pelotao(self):
        self.client.force_authenticate(self.integrante)
        response = self.client.post("/api/chat/conversas/", {
            "torcida": self.torcida.pk,
            "pelotao": self.pelotao.pk,
            "tipo": "grupo",
            "nome": "Resenha Norte",
            "participantes": [self.fora.pk],
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("participantes", response.data)

    def test_nao_permite_adicionar_membro_de_outro_pelotao(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/chat/conversas/", {
            "torcida": self.torcida.pk,
            "pelotao": self.pelotao.pk,
            "tipo": "grupo",
            "nome": "Grupo Norte",
            "participantes": [self.integrante.pk, self.fora.pk],
        }, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Conversa.objects.count(), 0)

    def test_conversa_de_pelotao_e_criada_com_membros_validos(self):
        self.client.force_authenticate(self.integrante)
        response = self.client.post("/api/chat/conversas/", {
            "torcida": self.torcida.pk,
            "pelotao": self.pelotao.pk,
            "tipo": "privada",
            "participantes": [self.segundo.pk],
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["pelotao"], self.pelotao.pk)


class LiveKitCallTokenTests(APITestCase):
    def setUp(self):
        from chat.models import ParticipanteConversa
        self.user = User.objects.create_user(
            username="livekit_member", password="Strong-Test-Password-2026!"
        )
        self.outsider = User.objects.create_user(
            username="livekit_outsider", password="Strong-Test-Password-2026!"
        )
        self.torcida = Torcida.objects.create(nome="LiveKit FC", slug="livekit-fc")
        Membro.objects.create(usuario=self.user, torcida=self.torcida, papel="membro")
        self.conversa = Conversa.objects.create(
            torcida=self.torcida, tipo=Conversa.Tipo.PRIVADA, criada_por=self.user
        )
        ParticipanteConversa.objects.create(conversa=self.conversa, usuario=self.user)

    def test_usuario_sem_participacao_nao_recebe_token(self):
        self.client.force_authenticate(self.outsider)
        response = self.client.post(
            f"/api/chat/conversas/{self.conversa.pk}/chamada/token/"
        )
        self.assertEqual(response.status_code, 404)

    @patch("chat.calls.api.AccessToken")
    @patch.dict("os.environ", {
        "LIVEKIT_URL": "https://calls.example.com/",
        "LIVEKIT_API_KEY": "test-key",
        "LIVEKIT_API_SECRET": "test-secret",
    })
    def test_url_https_e_convertida_para_wss_ao_emitir_token(self, access_token):
        token_builder = access_token.return_value
        token_builder.with_identity.return_value = token_builder
        token_builder.with_name.return_value = token_builder
        token_builder.with_ttl.return_value = token_builder
        token_builder.with_grants.return_value = token_builder
        token_builder.to_jwt.return_value = "token-de-teste"
        self.client.force_authenticate(self.user)
        response = self.client.post(
            f"/api/chat/conversas/{self.conversa.pk}/chamada/token/"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["server_url"], "wss://calls.example.com")
        self.assertEqual(response.data["token"], "token-de-teste")
