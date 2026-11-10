from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TorcidaViewSet
from .member_views import (
    ListaMembrosView,
    DetalheMembroView,
    CriarConviteView,
    AceitarConviteView,
    RevogarConviteView,
)
from .pelotao_views import ListaCriarPelotaoView, DetalhePelotaoView
from .audit_views import ListaAtividadesPelotaoView

router = DefaultRouter()
router.register("", TorcidaViewSet, basename="torcida")

urlpatterns = [
    path("convites/aceitar/", AceitarConviteView.as_view(), name="aceitar-convite"),
    path("<int:torcida_id>/atividades/", ListaAtividadesPelotaoView.as_view(), name="lista-atividades-pelotao"),
    path("<int:torcida_id>/pelotoes/", ListaCriarPelotaoView.as_view(), name="lista-criar-pelotoes"),
    path("<int:torcida_id>/pelotoes/<int:pelotao_id>/", DetalhePelotaoView.as_view(), name="detalhe-pelotao"),
    path("<int:torcida_id>/convites/", CriarConviteView.as_view(), name="criar-convite"),
    path(
        "<int:torcida_id>/convites/<int:convite_id>/revogar/",
        RevogarConviteView.as_view(),
        name="revogar-convite",
    ),
    path("<int:torcida_id>/membros/", ListaMembrosView.as_view(), name="lista-membros"),
    path(
        "<int:torcida_id>/membros/<int:membro_id>/",
        DetalheMembroView.as_view(),
        name="detalhe-membro",
    ),
    path("", include(router.urls)),
]
