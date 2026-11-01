from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PublicacaoViewSet,
    ComentarioViewSet,
    CurtidaView,
)

router = DefaultRouter()
router.register(
    "publicacoes",
    PublicacaoViewSet,
    basename="publicacao",
)

urlpatterns = [
    path(
        "publicacoes/<int:publicacao_id>/comentarios/",
        ComentarioViewSet.as_view({
            "get": "list",
            "post": "create",
        }),
        name="lista-comentarios",
    ),
    path(
        "publicacoes/<int:publicacao_id>/comentarios/<int:comentario_id>/",
        ComentarioViewSet.as_view({
            "get": "retrieve",
            "patch": "partial_update",
            "delete": "destroy",
        }),
        name="detalhe-comentario",
    ),
    path(
        "publicacoes/<int:publicacao_id>/curtida/",
        CurtidaView.as_view(),
        name="curtida-publicacao",
    ),
    path("", include(router.urls)),
]
