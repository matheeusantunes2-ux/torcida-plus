from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve
from community.media_views import PublicacaoImageView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/torcidas/", include("torcidas.urls")),
    path("api/comunidade/", include("community.urls")),
    path("api/chat/", include("chat.urls")),
    path("api/eventos/", include("events.urls")),
    path("api/loja/", include("store.urls")),
]

# As imagens enviadas pelos usuários precisam ser acessíveis também em produção.
# Em produção com armazenamento persistente/objeto, este caminho pode ser servido
# por um CDN; no momento, o Django atende os arquivos em MEDIA_ROOT.
urlpatterns += [
    re_path(
        r"^media/publicacoes/(?P<path>.+)$",
        PublicacaoImageView.as_view(),
        name="media-publicacao",
    ),
    # Fotos de perfil e imagens de produtos permanecem públicas conforme o
    # comportamento atual; imagens de publicações usam a rota assinada acima.
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]
