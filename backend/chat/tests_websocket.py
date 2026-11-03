from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from channels.testing import WebsocketCommunicator

from config.asgi import application
from torcidas.models import Membro, Torcida
from .models import Conversa, ParticipanteConversa

User = get_user_model()


@override_settings(CHANNEL_LAYERS={
    "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
})
class ChatWebSocketTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="ws_user", password="Senha-Forte-2026!")
        self.outro = User.objects.create_user(username="ws_outro", password="Senha-Forte-2026!")
        self.torcida = Torcida.objects.create(nome="WS Teste", slug="ws-teste")
        Membro.objects.create(usuario=self.user, torcida=self.torcida, papel="admin")
        Membro.objects.create(usuario=self.outro, torcida=self.torcida, papel="membro")
        self.conversa = Conversa.objects.create(
            torcida=self.torcida, tipo="privada", criada_por=self.user
        )
        ParticipanteConversa.objects.create(conversa=self.conversa, usuario=self.user)
        ParticipanteConversa.objects.create(conversa=self.conversa, usuario=self.outro)

    async def test_ticket_unico_autentica_e_envia_mensagem(self):
        ticket = "ticket-ws-teste"
        cache.set(f"chat:ws-ticket:{ticket}", self.user.pk, timeout=60)
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.conversa.pk}/?ticket={ticket}"
        )
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        await communicator.send_json_to({"conteudo": "Mensagem ao vivo"})
        response = await communicator.receive_json_from()
        self.assertEqual(response["conteudo"], "Mensagem ao vivo")
        await communicator.disconnect()
        self.assertIsNone(cache.get(f"chat:ws-ticket:{ticket}"))

    async def test_ticket_invalido_e_rejeitado(self):
        communicator = WebsocketCommunicator(
            application, f"/ws/chat/{self.conversa.pk}/?ticket=invalido"
        )
        connected, _ = await communicator.connect()
        self.assertFalse(connected)
