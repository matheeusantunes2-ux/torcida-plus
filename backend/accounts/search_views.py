from django.db.models import Q
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from torcidas.models import Membro
from events.models import Evento
from .models import Perfil


class BuscaGlobalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        termo = (request.query_params.get("q") or "").strip()[:80]
        if len(termo) < 2:
            return Response({"perfis": [], "eventos": []})

        torcidas_ids = Membro.objects.filter(usuario=request.user).values_list("torcida_id", flat=True)
        perfis = Perfil.objects.select_related("usuario").filter(
            usuario__membros_torcida__torcida_id__in=torcidas_ids
        ).filter(
            Q(usuario__username__icontains=termo) |
            Q(nome_exibicao__icontains=termo) |
            Q(biografia__icontains=termo)
        ).exclude(usuario=request.user).distinct()[:8]

        perfis_data = [{
            "username": p.usuario.username,
            "nome_exibicao": p.nome_exibicao or p.usuario.username,
            "biografia": p.biografia,
            "foto": request.build_absolute_uri(p.foto.url) if p.foto else None,
        } for p in perfis]

        eventos = Evento.objects.filter(
            torcida_id__in=torcidas_ids,
            status=Evento.Status.PUBLICADO,
        ).filter(
            Q(titulo__icontains=termo) |
            Q(descricao__icontains=termo) |
            Q(local__icontains=termo)
        ).select_related("torcida").order_by("inicio_em")[:8]

        eventos_data = [{
            "id": e.id,
            "titulo": e.titulo,
            "local": e.local,
            "inicio_em": e.inicio_em,
            "valor": str(e.valor),
            "torcida_nome": e.torcida.nome,
        } for e in eventos]
        return Response({"perfis": perfis_data, "eventos": eventos_data})
