from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import is_platform_admin
from .models import Torcida, Membro, Pelotao


class PelotaoSerializer(serializers.ModelSerializer):
    total_integrantes = serializers.IntegerField(source="membros.count", read_only=True)

    class Meta:
        model = Pelotao
        fields = ["id", "torcida", "nome", "slug", "descricao", "ativo", "total_integrantes", "criado_em"]
        read_only_fields = ["id", "torcida", "total_integrantes", "criado_em"]

    def validate_slug(self, value):
        return value.lower().strip()


def obter_torcida_membro(request, torcida_id):
    qs = Torcida.objects.all()
    if not is_platform_admin(request.user):
        qs = qs.filter(membros__usuario=request.user)
    return get_object_or_404(qs.distinct(), pk=torcida_id)


def exigir_gestor(request, torcida):
    if is_platform_admin(request.user):
        return
    membro = Membro.objects.filter(torcida=torcida, usuario=request.user).first()
    if not membro or membro.papel != Membro.Papel.ADMIN:
        raise PermissionDenied("Somente a administração da torcida pode gerenciar pelotões.")


class ListaCriarPelotaoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, torcida_id):
        torcida = obter_torcida_membro(request, torcida_id)
        qs = Pelotao.objects.filter(torcida=torcida, ativo=True).prefetch_related("membros")
        if not is_platform_admin(request.user):
            atual = Membro.objects.filter(torcida=torcida, usuario=request.user).first()
            if atual and atual.papel == Membro.Papel.LIDER_PELOTAO:
                if atual.pelotao_id is None:
                    raise PermissionDenied("Líder sem pelotão ativo não pode consultar a gestão.")
                qs = qs.filter(pk=atual.pelotao_id)
        return Response(PelotaoSerializer(qs, many=True).data)

    def post(self, request, torcida_id):
        torcida = obter_torcida_membro(request, torcida_id)
        exigir_gestor(request, torcida)
        serializer = PelotaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pelotao = serializer.save(torcida=torcida)
        return Response(PelotaoSerializer(pelotao).data, status=status.HTTP_201_CREATED)


class DetalhePelotaoView(APIView):
    permission_classes = [IsAuthenticated]

    def get_obj(self, request, torcida_id, pelotao_id):
        torcida = obter_torcida_membro(request, torcida_id)
        if not is_platform_admin(request.user):
            atual = Membro.objects.filter(torcida=torcida, usuario=request.user).first()
            if atual and atual.papel == Membro.Papel.LIDER_PELOTAO and atual.pelotao_id != pelotao_id:
                raise PermissionDenied("Você só pode acessar seu próprio pelotão.")
        return get_object_or_404(Pelotao, pk=pelotao_id, torcida=torcida)

    def get(self, request, torcida_id, pelotao_id):
        return Response(PelotaoSerializer(self.get_obj(request, torcida_id, pelotao_id)).data)

    def patch(self, request, torcida_id, pelotao_id):
        torcida = obter_torcida_membro(request, torcida_id)
        exigir_gestor(request, torcida)
        pelotao = get_object_or_404(Pelotao, pk=pelotao_id, torcida=torcida)
        serializer = PelotaoSerializer(pelotao, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, torcida_id, pelotao_id):
        torcida = obter_torcida_membro(request, torcida_id)
        exigir_gestor(request, torcida)
        pelotao = get_object_or_404(Pelotao, pk=pelotao_id, torcida=torcida)
        pelotao.ativo = False
        pelotao.save(update_fields=["ativo"])
        return Response(status=status.HTTP_204_NO_CONTENT)
