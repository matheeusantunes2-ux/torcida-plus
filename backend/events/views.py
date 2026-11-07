from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.permissions import is_platform_admin
from torcidas.models import Membro
from .models import Evento
from .serializers import EventoSerializer


class EventoViewSet(viewsets.ModelViewSet):
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Evento.objects.select_related("torcida", "criado_por")
        if is_platform_admin(self.request.user):
            return queryset
        usuario = self.request.user
        return queryset.filter(
            Q(torcida__membros__usuario=usuario,
              torcida__membros__papel__in=[Membro.Papel.ADMIN, Membro.Papel.MODERADOR])
            | Q(torcida__membros__usuario=usuario,
                status__in=[Evento.Status.PUBLICADO, Evento.Status.ENCERRADO])
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)

    def perform_update(self, serializer):
        serializer.save()
