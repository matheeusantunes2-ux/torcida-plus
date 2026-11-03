from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from .models import Conversa, ParticipanteConversa, Mensagem


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversa_id = self.scope["url_route"]["kwargs"]["conversa_id"]
        self.user = self.scope["user"]
        if not await self.usuario_participa():
            await self.close(code=4403)
            return
        self.group_name = f"chat_{self.conversa_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        texto = content.get("conteudo") if isinstance(content, dict) else None
        if not isinstance(texto, str) or not texto.strip() or len(texto) > 4000:
            await self.send_json({"tipo": "erro", "mensagem": "Mensagem inválida."})
            return
        mensagem = await self.salvar_mensagem(texto.strip())
        await self.channel_layer.group_send(
            self.group_name, {"type": "chat.message", "mensagem": mensagem}
        )

    async def chat_message(self, event):
        await self.send_json({"tipo": "mensagem", **event["mensagem"]})

    @database_sync_to_async
    def usuario_participa(self):
        return ParticipanteConversa.objects.filter(
            conversa_id=self.conversa_id, usuario=self.user, ativo=True,
            conversa__torcida__membros__usuario=self.user,
        ).exists()

    @database_sync_to_async
    def salvar_mensagem(self, texto):
        conversa = Conversa.objects.get(pk=self.conversa_id)
        mensagem = Mensagem.objects.create(
            conversa=conversa, autor=self.user, conteudo=texto
        )
        Conversa.objects.filter(pk=conversa.pk).update(atualizada_em=timezone.now())
        return {
            "id": mensagem.pk, "conversa_id": conversa.pk,
            "autor_id": self.user.pk, "autor_username": self.user.get_username(),
            "conteudo": mensagem.conteudo, "criada_em": mensagem.criada_em.isoformat(),
        }
