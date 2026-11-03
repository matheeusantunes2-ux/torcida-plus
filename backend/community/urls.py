from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PublicacaoViewSet,
    ComentarioViewSet,
    CurtidaView,
    NotificacaoViewSet,
)

router = DefaultRouter()
router.register(
    "publicacoes",
    PublicacaoViewSet,
    basename="publicacao",
)

notificacoes = NotificacaoViewSet.as_view({'get': 'list'})
marcar_todas = NotificacaoViewSet.as_view({'post': 'mark_all_read'})
marcar_uma = NotificacaoViewSet.as_view({'post': 'mark_one_read'})

urlpatterns = [
    path('notificacoes/', notificacoes, name='notificacoes'),
    path('notificacoes/ler-todas/', marcar_todas, name='notificacoes-ler-todas'),
    path('notificacoes/<int:pk>/ler/', marcar_uma, name='notificacao-ler'),
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
