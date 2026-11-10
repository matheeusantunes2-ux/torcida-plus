from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import is_platform_admin
from .models import AtividadePelotao, Membro, Torcida


def registrar_atividade(torcida, ator, acao, descricao, pelotao=None):
    # Nunca registrar tokens, credenciais ou conteúdo de mensagens.
    return AtividadePelotao.objects.create(
        torcida=torcida, pelotao=pelotao, ator=ator,
        acao=acao[:48], descricao=descricao[:300],
    )


class AtividadePelotaoSerializer(serializers.ModelSerializer):
    ator_username = serializers.CharField(source="ator.username", read_only=True, allow_null=True)
    pelotao_nome = serializers.CharField(source="pelotao.nome", read_only=True, allow_null=True)

    class Meta:
        model = AtividadePelotao
        fields = ["id", "acao", "descricao", "ator_username", "pelotao", "pelotao_nome", "criado_em"]


class ListaAtividadesPelotaoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, torcida_id):
        qs_torcida = Torcida.objects.all()
        if not is_platform_admin(request.user):
            qs_torcida = qs_torcida.filter(membros__usuario=request.user)
        torcida = qs_torcida.distinct().filter(pk=torcida_id).first()
        if torcida is None:
            from django.shortcuts import get_object_or_404
            return get_object_or_404(qs_torcida.distinct(), pk=torcida_id)
        atividades = AtividadePelotao.objects.filter(torcida=torcida).select_related("ator", "pelotao")
        atual = Membro.objects.filter(torcida=torcida, usuario=request.user).first()
        if not is_platform_admin(request.user) and atual and atual.papel == Membro.Papel.LIDER_PELOTAO:
            if not atual.pelotao_id:
                raise PermissionDenied("Líder sem pelotão não pode consultar atividades.")
            atividades = atividades.filter(pelotao_id=atual.pelotao_id)
        pelotao_id = request.query_params.get("pelotao_id")
        if pelotao_id:
            if not is_platform_admin(request.user) and (not atual or atual.papel != Membro.Papel.ADMIN):
                raise PermissionDenied("Somente a administração pode filtrar outros pelotões.")
            atividades = atividades.filter(pelotao_id=pelotao_id)
        try:
            limit = min(max(int(request.query_params.get("limit", 30)), 1), 100)
            offset = max(int(request.query_params.get("offset", 0)), 0)
        except (TypeError, ValueError):
            from rest_framework.exceptions import ValidationError
            raise ValidationError("Paginação inválida.")
        total = atividades.count()
        page = atividades[offset:offset + limit]
        return Response({"count": total, "next_offset": offset + limit if offset + limit < total else None,
                         "results": AtividadePelotaoSerializer(page, many=True).data})
