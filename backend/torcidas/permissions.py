from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import Membro


class PodeAcessarTorcida(BasePermission):
    """
    Membros podem consultar a torcida.
    Apenas administradores podem modificá-la ou excluí-la.
    """

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        membro = Membro.objects.filter(
            torcida=obj,
            usuario=request.user,
        ).first()

        # Quem não participa da torcida não acessa seus detalhes.
        if membro is None:
            return False

        # Participantes podem consultar os dados da torcida.
        if request.method in SAFE_METHODS:
            return True

        # Somente administradores podem alterar ou excluir.
        return membro.papel == "admin"
