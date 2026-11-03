from django.urls import path

from .views import ListaCriarConversaView, ListaCriarMensagemView

urlpatterns = [
    path("conversas/", ListaCriarConversaView.as_view(), name="lista-criar-conversas"),
    path("conversas/<int:conversa_id>/mensagens/", ListaCriarMensagemView.as_view(), name="lista-criar-mensagens"),
]
