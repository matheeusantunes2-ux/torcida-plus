from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.core.cache import cache
from django.utils import timezone

from .models import Conversa, ParticipanteConversa, Mensagem, LeituraMensagem
from accounts.permissions import is_platform_admin


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.conversa_id = self.scope["url_route"]["kwargs"]["conversa_id"]
        self.user = self.scope["user"]
        if not await self.usuario_participa():
            await self.close(code=4403)
            return
        self.group_name = f"chat_{self.conversa_id}"
        self.presence_key = f"chat:online:{self.conversa_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.channel_layer.group_add(f"user_{self.user.pk}", self.channel_name)
        await self.accept()
        await self.presenca(True)
        await self.channel_layer.group_send(
            self.group_name,
            {"type": "chat.presence", "usuario_id": self.user.pk, "online": True},
        )

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            await self.channel_layer.group_discard(f"user_{self.user.pk}", self.channel_name)
            await self.presenca(False)
            await self.channel_layer.group_send(
                self.group_name,
                {"type": "chat.presence", "usuario_id": self.user.pk, "online": False},
            )

    async def receive_json(self, content, **kwargs):
        if not isinstance(content, dict):
            await self.send_json({"tipo": "erro", "mensagem": "Evento inválido."})
            return
        acao = content.get("acao", "mensagem")
        if acao == "digitando":
            await self.channel_layer.group_send(self.group_name, {
                "type": "chat.typing", "usuario_id": self.user.pk,
                "digitando": bool(content.get("digitando", True)),
            })
            return
        if acao == "lida":
            mensagem_id = content.get("mensagem_id")
            if not isinstance(mensagem_id, int):
                await self.send_json({"tipo": "erro", "mensagem": "mensagem_id inválido."})
                return
            resultado = await self.marcar_lida(mensagem_id)
            if resultado:
                await self.channel_layer.group_send(
                    f"user_{resultado['autor_id']}",
                    {"type": "chat.read", "mensagem_id": mensagem_id,
                     "usuario_id": self.user.pk, "lida_em": resultado["lida_em"]},
                )
            return
        texto = content.get("conteudo")
        if not isinstance(texto, str) or not texto.strip() or len(texto) > 4000:
            await self.send_json({"tipo": "erro", "mensagem": "Mensagem inválida."})
            return
        mensagem = await self.salvar_mensagem(texto.strip())
        await self.channel_layer.group_send(
            self.group_name, {"type": "chat.message", "mensagem": mensagem}
        )

    async def chat_message(self, event):
        await self.send_json({"tipo": "mensagem", **event["mensagem"]})

    async def chat_presence(self, event):
        if event["usuario_id"] != self.user.pk:
            await self.send_json({"tipo": "presenca", **event})

    async def chat_typing(self, event):
        if event["usuario_id"] != self.user.pk:
            await self.send_json({"tipo": "digitando", **event})

    async def chat_read(self, event):
        await self.send_json({"tipo": "leitura", **event})

    @database_sync_to_async
    def usuario_participa(self):
        if is_platform_admin(self.user):
            return Conversa.objects.filter(pk=self.conversa_id).exists()
        return ParticipanteConversa.objects.filter(
            conversa_id=self.conversa_id, usuario=self.user, ativo=True,
            conversa__torcida__membros__usuario=self.user,
        ).exists()

    @database_sync_to_async
    def presenca(self, online):
        key = f"chat:online:{self.conversa_id}"
        online_ids = set(cache.get(key, []))
        if online:
            online_ids.add(self.user.pk)
        else:
            online_ids.discard(self.user.pk)
        cache.set(key, list(online_ids), timeout=120)

    @database_sync_to_async
    def marcar_lida(self, mensagem_id):
        try:
            mensagem = Mensagem.objects.get(pk=mensagem_id, conversa_id=self.conversa_id)
        except Mensagem.DoesNotExist:
            return None
        if mensagem.autor_id == self.user.pk:
            return None
        leitura, _ = LeituraMensagem.objects.get_or_create(
            mensagem=mensagem, usuario=self.user
        )
        return {"autor_id": mensagem.autor_id, "lida_em": leitura.lida_em.isoformat()}

    @database_sync_to_async
    def salvar_mensagem(self, texto):
        conversa = Conversa.objects.get(pk=self.conversa_id)
        mensagem = Mensagem.objects.create(conversa=conversa, autor=self.user, conteudo=texto)
        Conversa.objects.filter(pk=conversa.pk).update(atualizada_em=timezone.now())
        return {
            "id": mensagem.pk, "conversa_id": conversa.pk,
            "autor_id": self.user.pk, "autor_username": self.user.get_username(),
            "conteudo": mensagem.conteudo, "criada_em": mensagem.criada_em.isoformat(),
            "status": "enviada",
        }
