from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
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
        torcidas_gerenciadas = Membro.objects.filter(
            usuario=usuario,
            papel__in=[Membro.Papel.ADMIN, Membro.Papel.MODERADOR],
        ).values("torcida_id")
        torcidas_membro = Membro.objects.filter(
            usuario=usuario,
        ).values("torcida_id")
        return queryset.filter(
            Q(torcida_id__in=torcidas_gerenciadas)
            | Q(
                torcida_id__in=torcidas_membro,
                status__in=[Evento.Status.PUBLICADO, Evento.Status.ENCERRADO],
            )
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        evento = self.get_object()
        if not is_platform_admin(request.user):
            gerente = Membro.objects.filter(
                torcida=evento.torcida,
                usuario=request.user,
                papel__in=[Membro.Papel.ADMIN, Membro.Papel.MODERADOR],
            ).exists()
            if not gerente:
                raise PermissionDenied("Somente administradores e moderadores podem excluir eventos.")
        evento.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
