from rest_framework.viewsets import ModelViewSet
from accounts.permissions import is_platform_admin
from .models import Torcida, Membro
from .serializers import TorcidaSerializer
from .permissions import PodeAcessarTorcida

class TorcidaViewSet(ModelViewSet):
    serializer_class = TorcidaSerializer
    permission_classes = [PodeAcessarTorcida]
    def get_queryset(self):
        queryset = Torcida.objects.all()
        if is_platform_admin(self.request.user):
            return queryset
        return queryset.filter(membros__usuario=self.request.user).distinct()
    def perform_create(self, serializer):
        torcida = serializer.save()
        if not is_platform_admin(self.request.user):
            Membro.objects.create(usuario=self.request.user, torcida=torcida, papel="admin")
