import secrets

from django.core.cache import cache
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class CriarTicketWebSocketView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ticket = secrets.token_urlsafe(32)
        cache.set(f"chat:ws-ticket:{ticket}", request.user.pk, timeout=60)
        return Response({"ticket": ticket, "expira_em_segundos": 60})
