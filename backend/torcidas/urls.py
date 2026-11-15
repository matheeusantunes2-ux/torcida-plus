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
from .associacao_views import (PlanosAssociacaoView, SolicitarAssociacaoView, MinhasAssociacoesView, GestaoAssociacoesView, CarteirinhaQRView, ValidarCarteirinhaQRView)

router = DefaultRouter()
router.register("", TorcidaViewSet, basename="torcida")

urlpatterns = [
    path("associacoes/minhas/", MinhasAssociacoesView.as_view(), name="minhas-associacoes"),
    path("associacoes/<int:associacao_id>/carteirinha-qr/", CarteirinhaQRView.as_view(), name="carteirinha-qr"),
    path("<int:torcida_id>/associacoes/planos/", PlanosAssociacaoView.as_view(), name="planos-associacao"),
    path("<int:torcida_id>/associacoes/solicitar/", SolicitarAssociacaoView.as_view(), name="solicitar-associacao"),
    path("<int:torcida_id>/associacoes/", GestaoAssociacoesView.as_view(), name="gestao-associacoes"),
    path("<int:torcida_id>/associacoes/<int:associacao_id>/", GestaoAssociacoesView.as_view(), name="detalhe-associacao"),
    path("<int:torcida_id>/associacoes/validar-qr/", ValidarCarteirinhaQRView.as_view(), name="validar-carteirinha-qr"),
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
