from django.urls import path

from .views import EnviarAnexoMensagemView, ListaCriarConversaView, ListaCriarMensagemView, ObterUrlAnexoView
from .tickets import CriarTicketWebSocketView
from .calls import CriarTokenSalaView

urlpatterns = [
    path("ws-ticket/", CriarTicketWebSocketView.as_view(), name="criar-ticket-websocket"),
    path("conversas/", ListaCriarConversaView.as_view(), name="lista-criar-conversas"),
    path("conversas/<int:conversa_id>/mensagens/", ListaCriarMensagemView.as_view(), name="lista-criar-mensagens"),
    path("conversas/<int:conversa_id>/anexos/", EnviarAnexoMensagemView.as_view(), name="enviar-anexo-mensagem"),
    path("anexos/<int:anexo_id>/url/", ObterUrlAnexoView.as_view(), name="chat-anexo-url"),
    path("conversas/<int:conversa_id>/chamada/token/", CriarTokenSalaView.as_view(), name="criar-token-sala"),
]
