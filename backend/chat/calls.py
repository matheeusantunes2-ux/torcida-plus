import os
from datetime import timedelta

from livekit import api
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversa, ParticipanteConversa


class CriarTokenSalaView(APIView):
    """Emite credencial curta para entrar na sala de vídeo da conversa."""
    permission_classes = [IsAuthenticated]

    def post(self, request, conversa_id):
        participante = ParticipanteConversa.objects.filter(
            conversa_id=conversa_id,
            usuario=request.user,
            ativo=True,
            conversa__torcida__membros__usuario=request.user,
        ).select_related("conversa").first()
        if not participante:
            return Response(
                {"detail": "Você não tem acesso a esta conversa."},
                status=status.HTTP_404_NOT_FOUND,
            )

        server_url = os.getenv("LIVEKIT_URL")
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        if not all((server_url, api_key, api_secret)):
            return Response(
                {"detail": "Serviço de chamadas ainda não configurado."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        room_name = f"torcida-conversa-{conversa_id}"
        token = (
            api.AccessToken(api_key, api_secret)
            .with_identity(str(request.user.pk))
            .with_name(request.user.get_username())
            .with_ttl(timedelta(minutes=30))
            .with_grants(api.VideoGrants(
                room_join=True,
                room=room_name,
                can_publish=True,
                can_subscribe=True,
                can_publish_data=True,
            ))
        )
        return Response({
            "server_url": server_url,
            "room": room_name,
            "token": token.to_jwt(),
            "expires_in": 1800,
            "provider": "livekit",
        })
