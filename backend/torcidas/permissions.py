from rest_framework.permissions import BasePermission, SAFE_METHODS
from accounts.permissions import is_platform_admin
from .models import Membro

class PodeAcessarTorcida(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
    def has_object_permission(self, request, view, obj):
        if is_platform_admin(request.user):
            return True
        membro = Membro.objects.filter(torcida=obj, usuario=request.user).first()
        if membro is None:
            return False
        if request.method in SAFE_METHODS:
            return True
        return membro.papel == "admin"
