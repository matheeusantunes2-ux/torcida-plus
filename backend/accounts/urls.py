from django.urls import path

from .views import CadastroView, MeuPerfilView, PerfilPublicoView
from .platform_admin_views import PlatformAdminOverviewView, PlatformAdminUsersView, PlatformAdminTorcidasView, PlatformAdminUserStatusView, PlatformAdminTorcidaDetailView

urlpatterns = [
    path("platform-admin/overview/", PlatformAdminOverviewView.as_view(), name="platform-admin-overview"),
    path("platform-admin/users/", PlatformAdminUsersView.as_view(), name="platform-admin-users"),
    path("platform-admin/users/<int:user_id>/status/", PlatformAdminUserStatusView.as_view(), name="platform-admin-user-status"),
    path("platform-admin/torcidas/", PlatformAdminTorcidasView.as_view(), name="platform-admin-torcidas"),
    path("platform-admin/torcidas/<int:torcida_id>/", PlatformAdminTorcidaDetailView.as_view(), name="platform-admin-torcida-detail"),
    path("cadastro/", CadastroView.as_view(), name="cadastro"),
    path("perfil/", MeuPerfilView.as_view(), name="meu-perfil"),
    path(
        "perfil/<str:username>/",
        PerfilPublicoView.as_view(),
        name="perfil-publico",
    ),
]
