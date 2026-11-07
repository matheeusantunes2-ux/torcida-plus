from rest_framework.permissions import BasePermission, SAFE_METHODS
from accounts.permissions import is_platform_admin


class AutorPodeEditarPublicacao(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if is_platform_admin(request.user):
            return True
        if request.method in SAFE_METHODS:
            return True
        return obj.autor_id == request.user.id
