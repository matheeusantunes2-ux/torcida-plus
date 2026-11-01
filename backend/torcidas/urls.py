from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TorcidaViewSet
from .member_views import ListaMembrosView, DetalheMembroView

router = DefaultRouter()
router.register("", TorcidaViewSet, basename="torcida")

urlpatterns = [
    path(
        "<int:torcida_id>/membros/",
        ListaMembrosView.as_view(),
        name="lista-membros",
    ),
    path(
        "<int:torcida_id>/membros/<int:membro_id>/",
        DetalheMembroView.as_view(),
        name="detalhe-membro",
    ),
    path("", include(router.urls)),
]
