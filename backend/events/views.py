from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from torcidas.models import Membro
from .models import Evento
from .serializers import EventoSerializer


class EventoViewSet(viewsets.ModelViewSet):
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        usuario = self.request.user
        return Evento.objects.filter(torcida__membros__usuario=usuario).select_related("torcida", "criado_por").distinct()

    def perform_create(self, serializer):
        torcida = serializer.validated_data["torcida"]
        membro = Membro.objects.filter(torcida=torcida, usuario=self.request.user).first()
        if not membro or membro.papel not in {"admin", "moderador"}:
            raise PermissionError("Apenas moderadores/admins podem criar eventos.")
        serializer.save(criado_por=self.request.user)

