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
