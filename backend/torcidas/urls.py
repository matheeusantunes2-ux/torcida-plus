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

router = DefaultRouter()
router.register("", TorcidaViewSet, basename="torcida")

urlpatterns = [
    path("convites/aceitar/", AceitarConviteView.as_view(), name="aceitar-convite"),
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
