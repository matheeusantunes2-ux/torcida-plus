from django.urls import path

from .views import CadastroView, MeuPerfilView, PerfilPublicoView

urlpatterns = [
    path("cadastro/", CadastroView.as_view(), name="cadastro"),
    path("perfil/", MeuPerfilView.as_view(), name="meu-perfil"),
    path(
        "perfil/<str:username>/",
        PerfilPublicoView.as_view(),
        name="perfil-publico",
    ),
]
