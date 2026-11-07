"""Helpers centralizados de autorização para administradores da plataforma."""
def is_platform_admin(user):
    return bool(user and getattr(user, "is_authenticated", False) and getattr(user, "is_active", False) and getattr(user, "is_superuser", False))
