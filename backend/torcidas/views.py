from rest_framework.viewsets import ModelViewSet

from .models import Torcida, Membro
from .serializers import TorcidaSerializer
from .permissions import PodeAcessarTorcida


class TorcidaViewSet(ModelViewSet):
    serializer_class = TorcidaSerializer
    permission_classes = [PodeAcessarTorcida]

    def get_queryset(self):
        return Torcida.objects.filter(
            membros__usuario=self.request.user
        ).distinct()

    def perform_create(self, serializer):
        torcida = serializer.save()

        Membro.objects.create(
            usuario=self.request.user,
            torcida=torcida,
            papel="admin",
        )
