import hashlib
import secrets
from datetime import timedelta
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import is_platform_admin
from .models import Torcida, Membro, ConviteTorcida, Pelotao
from community.models import Notificacao
from .member_serializers import MembroSerializer
from .audit_views import registrar_atividade

def obter_torcida(request, torcida_id):
    queryset = Torcida.objects.all()
    if not is_platform_admin(request.user):
        queryset = queryset.filter(membros__usuario=request.user)
    return get_object_or_404(queryset.distinct(), pk=torcida_id)

def exigir_admin(request, torcida):
    if is_platform_admin(request.user):
        return
    membro = Membro.objects.filter(torcida=torcida, usuario=request.user).first()
    if membro is None or membro.papel != Membro.Papel.ADMIN:
        raise PermissionDenied("Somente o administrador desta torcida pode executar esta ação.")


def obter_gestor(request, torcida):
    if is_platform_admin(request.user):
        return None
    gestor = Membro.objects.filter(torcida=torcida, usuario=request.user).select_related("pelotao").first()
    if gestor is None or gestor.papel not in (Membro.Papel.ADMIN, Membro.Papel.LIDER_PELOTAO):
        raise PermissionDenied("Você não tem permissão para gerenciar integrantes.")
    if gestor.papel == Membro.Papel.LIDER_PELOTAO and (gestor.pelotao is None or not gestor.pelotao.ativo):
        raise PermissionDenied("Líder sem pelotão ativo não pode administrar integrantes.")
    return gestor


def exigir_alvo_do_gestor(gestor, alvo):
    if gestor is not None and gestor.papel == Membro.Papel.LIDER_PELOTAO:
        if alvo.pelotao_id != gestor.pelotao_id:
            raise PermissionDenied("Você só pode administrar integrantes do seu próprio pelotão.")
        if alvo.papel in (Membro.Papel.ADMIN, Membro.Papel.LIDER_PELOTAO):
            raise PermissionDenied("Líderes não podem administrar administradores ou outros líderes.")

class ListaMembrosView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, torcida_id):
        torcida = obter_torcida(request, torcida_id)
        membros = Membro.objects.filter(torcida=torcida).select_related("usuario", "pelotao").order_by("id")
        if not is_platform_admin(request.user):
            atual = Membro.objects.filter(torcida=torcida, usuario=request.user).first()
            if atual and atual.papel == Membro.Papel.LIDER_PELOTAO:
                if atual.pelotao_id is None:
                    raise PermissionDenied("Líder sem pelotão ativo não pode consultar integrantes.")
                membros = membros.filter(pelotao_id=atual.pelotao_id)
        return Response(MembroSerializer(membros, many=True).data)

class CriarConviteView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, torcida_id):
        torcida = obter_torcida(request, torcida_id)
        gestor = obter_gestor(request, torcida)
        papel = request.data.get("papel", Membro.Papel.MEMBRO)
        pelotao = None
        pelotao_id = request.data.get("pelotao_id")
        if gestor is not None and gestor.papel == Membro.Papel.LIDER_PELOTAO:
            if papel != Membro.Papel.MEMBRO or str(pelotao_id) != str(gestor.pelotao_id):
                raise PermissionDenied("Líderes só podem convidar membros para o próprio pelotão.")
            pelotao = gestor.pelotao
        else:
            if papel not in (Membro.Papel.MEMBRO, Membro.Papel.MODERADOR):
                raise ValidationError({"papel": "Convites administrativos não podem ser criados por este endpoint."})
            if pelotao_id not in (None, ""):
                pelotao = get_object_or_404(Pelotao, pk=pelotao_id, torcida=torcida, ativo=True)
        try:
            dias = int(request.data.get("validade_dias", 7)); limite = int(request.data.get("limite_usos", 1))
        except (TypeError, ValueError):
            raise ValidationError("Validade e limite de usos devem ser números inteiros.")
        if not 1 <= dias <= 30 or not 1 <= limite <= 100:
            raise ValidationError("Validade: 1–30 dias; limite de usos: 1–100.")
        token = secrets.token_urlsafe(32)
        convite = ConviteTorcida.objects.create(torcida=torcida, criado_por=request.user, token_hash=hashlib.sha256(token.encode()).hexdigest(), papel=papel, pelotao=pelotao, expira_em=timezone.now()+timedelta(days=dias), limite_usos=limite)
        registrar_atividade(torcida, request.user, 'convite_criado', f'Convite criado para {pelotao.nome if pelotao else "a torcida"}.', pelotao)
        return Response({"id":convite.pk,"token":token,"torcida":torcida.nome,"papel":convite.papel,"expira_em":convite.expira_em,"limite_usos":convite.limite_usos,"pelotao":convite.pelotao.nome if convite.pelotao else None},status=status.HTTP_201_CREATED)

class AceitarConviteView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        token=request.data.get("token","")
        if not isinstance(token,str) or not token or len(token)>200: raise ValidationError({"token":"Informe um convite válido."})
        try:
            with transaction.atomic():
                convite=ConviteTorcida.objects.select_for_update().get(token_hash=hashlib.sha256(token.encode()).hexdigest())
                if not convite.ativo: raise ValidationError({"token":"Convite expirado, revogado ou esgotado."})
                if Membro.objects.filter(torcida=convite.torcida,usuario=request.user).exists(): raise ValidationError("Você já participa desta torcida.")
                membro=Membro.objects.create(torcida=convite.torcida,usuario=request.user,papel=convite.papel,pelotao=convite.pelotao)
                convite.usos+=1; convite.save(update_fields=["usos"])
                registrar_atividade(convite.torcida, request.user, "membro_entrou", f"{request.user.username} entrou por convite.", convite.pelotao)
                if convite.criado_por_id != request.user.id:
                    Notificacao.objects.create(destinatario=convite.criado_por,ator=request.user,tipo=Notificacao.Tipo.CONVITE,texto=f"{request.user.username} entrou no pelotão {convite.pelotao.nome}." if convite.pelotao else f"{request.user.username} entrou na torcida {convite.torcida.nome}.",referencia=f"torcida:{convite.torcida_id}")
        except ConviteTorcida.DoesNotExist: raise ValidationError({"token":"Convite inválido."})
        except IntegrityError: raise ValidationError("Não foi possível aceitar este convite.")
        return Response({"mensagem":"Você entrou na torcida.","membro":MembroSerializer(membro).data},status=status.HTTP_201_CREATED)

class RevogarConviteView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, torcida_id, convite_id):
        torcida=obter_torcida(request,torcida_id); exigir_admin(request,torcida)
        convite=get_object_or_404(ConviteTorcida,pk=convite_id,torcida=torcida)
        if convite.revogado_em is None:
            convite.revogado_em=timezone.now(); convite.save(update_fields=["revogado_em"])
            registrar_atividade(torcida, request.user, "convite_revogado", f"Convite #{convite.pk} revogado.", convite.pelotao)
        return Response({"mensagem":"Convite revogado."})

class DetalheMembroView(APIView):
    permission_classes = [IsAuthenticated]
    def obter_membro(self,torcida,membro_id):
        return get_object_or_404(Membro.objects.select_related("usuario").filter(torcida=torcida),pk=membro_id)
    def patch(self,request,torcida_id,membro_id):
        torcida=obter_torcida(request,torcida_id)
        gestor=obter_gestor(request,torcida)
        membro=self.obter_membro(torcida,membro_id)
        exigir_alvo_do_gestor(gestor,membro)
        if gestor is not None and gestor.papel == Membro.Papel.LIDER_PELOTAO:
            raise PermissionDenied("Líderes podem convidar e remover integrantes do próprio pelotão, mas não alterar cargos ou vínculos.")
        if membro.papel == Membro.Papel.ADMIN: raise ValidationError("A transferência de administração exige procedimento específico.")
        papel=request.data.get("papel", membro.papel)
        if papel not in (Membro.Papel.MEMBRO,Membro.Papel.MODERADOR,Membro.Papel.LIDER_PELOTAO):
            raise ValidationError({"papel":"Use membro, moderador ou lider_pelotao."})
        pelotao_id=request.data.get("pelotao_id", ...)
        novo_pelotao = membro.pelotao
        if pelotao_id is not ...:
            novo_pelotao = None if pelotao_id in (None, "") else get_object_or_404(Pelotao, pk=pelotao_id, torcida=torcida, ativo=True)
        if papel == Membro.Papel.LIDER_PELOTAO and novo_pelotao is None:
            raise ValidationError({"pelotao_id":"Um líder precisa estar vinculado a um pelotão ativo."})
        papel_anterior, pelotao_anterior = membro.papel, membro.pelotao
        membro.papel=papel
        membro.pelotao=novo_pelotao
        membro.save(update_fields=["papel", "pelotao"])
        if papel != papel_anterior and (papel == Membro.Papel.LIDER_PELOTAO or papel_anterior == Membro.Papel.LIDER_PELOTAO):
            acao = "lideranca_alterada"
        elif novo_pelotao != pelotao_anterior:
            acao = "vinculo_alterado"
        else:
            acao = "cargo_alterado"
        descricao = f"Vínculo de {membro.usuario.username} atualizado: {papel_anterior} para {papel}; pelotão {pelotao_anterior.nome if pelotao_anterior else 'nenhum'} para {novo_pelotao.nome if novo_pelotao else 'nenhum'}."
        registrar_atividade(torcida, request.user, acao, descricao, novo_pelotao or pelotao_anterior)
        return Response(MembroSerializer(membro).data)

    def delete(self,request,torcida_id,membro_id):
        torcida=obter_torcida(request,torcida_id)
        gestor=obter_gestor(request,torcida)
        membro=self.obter_membro(torcida,membro_id)
        exigir_alvo_do_gestor(gestor,membro)
        if membro.papel == Membro.Papel.ADMIN: raise ValidationError("Não é permitido remover um administrador por este endpoint.")
        nome, pelotao = membro.usuario.username, membro.pelotao
        membro.delete()
        registrar_atividade(torcida, request.user, "membro_removido", f"{nome} foi removido do pelotão.", pelotao)
        return Response(status=status.HTTP_204_NO_CONTENT)
