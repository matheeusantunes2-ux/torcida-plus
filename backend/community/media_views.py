import mimetypes

from django.contrib.auth import get_user_model
from django.core import signing
from django.http import FileResponse, Http404
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from accounts.permissions import is_platform_admin
from community.models import Publicacao
from torcidas.models import Membro


@method_decorator(never_cache, name="dispatch")
class PublicacaoImageView(View):
    """Entrega imagem de publicação somente a membro atual ou admin global."""

    def get(self, request, path):
        token = request.GET.get("token", "")
        try:
            dados = signing.loads(
                token,
                salt="torcida-publicacao-media-v1",
                max_age=300,
            )
        except signing.BadSignature:
            raise Http404

        if dados.get("arquivo") != f"publicacoes/{path}":
            raise Http404

        publicacao = Publicacao.objects.select_related("torcida").filter(
            pk=dados.get("publicacao_id"),
            imagem=f"publicacoes/{path}",
            status=Publicacao.Status.APROVADA,
        ).first()
        if not publicacao:
            raise Http404

        usuario = get_user_model().objects.filter(
            pk=dados.get("usuario_id"),
            is_active=True,
        ).first()
        if not usuario:
            raise Http404

        autorizado = is_platform_admin(usuario) or Membro.objects.filter(
            torcida=publicacao.torcida,
            usuario=usuario,
        ).exists()
        if not autorizado:
            raise Http404

        try:
            arquivo = publicacao.imagem.open("rb")
        except (FileNotFoundError, OSError, ValueError):
            raise Http404

        content_type, _ = mimetypes.guess_type(publicacao.imagem.name)
        response = FileResponse(arquivo, content_type=content_type or "application/octet-stream")
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response
