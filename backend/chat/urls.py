from django.urls import path

from .views import ListaCriarConversaView, ListaCriarMensagemView
from .tickets import CriarTicketWebSocketView

urlpatterns = [
    path("ws-ticket/", CriarTicketWebSocketView.as_view(), name="criar-ticket-websocket"),
    path("conversas/", ListaCriarConversaView.as_view(), name="lista-criar-conversas"),
    path("conversas/<int:conversa_id>/mensagens/", ListaCriarMensagemView.as_view(), name="lista-criar-mensagens"),
]
