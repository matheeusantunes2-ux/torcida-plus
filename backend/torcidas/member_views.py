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
from .models import Torcida, Membro, ConviteTorcida
from community.models import Notificacao
from .member_serializers import MembroSerializer

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
        raise PermissionDenied("Somente o administrador desta torcida pode gerenciar membros.")

class ListaMembrosView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, torcida_id):
        torcida = obter_torcida(request, torcida_id)
        membros = Membro.objects.filter(torcida=torcida).select_related("usuario").order_by("id")
        return Response(MembroSerializer(membros, many=True).data)

class CriarConviteView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, torcida_id):
        torcida = obter_torcida(request, torcida_id); exigir_admin(request, torcida)
        papel = request.data.get("papel", Membro.Papel.MEMBRO)
        if papel not in (Membro.Papel.MEMBRO, Membro.Papel.MODERADOR):
            raise ValidationError({"papel": "Use 'membro' ou 'moderador'."})
        try:
            dias = int(request.data.get("validade_dias", 7)); limite = int(request.data.get("limite_usos", 1))
        except (TypeError, ValueError):
            raise ValidationError("Validade e limite de usos devem ser números inteiros.")
        if not 1 <= dias <= 30 or not 1 <= limite <= 100:
            raise ValidationError("Validade: 1–30 dias; limite de usos: 1–100.")
        token = secrets.token_urlsafe(32)
        convite = ConviteTorcida.objects.create(torcida=torcida, criado_por=request.user, token_hash=hashlib.sha256(token.encode()).hexdigest(), papel=papel, expira_em=timezone.now()+timedelta(days=dias), limite_usos=limite)
        return Response({"id":convite.pk,"token":token,"torcida":torcida.nome,"papel":convite.papel,"expira_em":convite.expira_em,"limite_usos":convite.limite_usos},status=status.HTTP_201_CREATED)

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
                membro=Membro.objects.create(torcida=convite.torcida,usuario=request.user,papel=convite.papel)
                convite.usos+=1; convite.save(update_fields=["usos"])
                if convite.criado_por_id != request.user.id:
                    Notificacao.objects.create(destinatario=convite.criado_por,ator=request.user,tipo=Notificacao.Tipo.CONVITE,texto=f"{request.user.username} entrou na torcida {convite.torcida.nome}.",referencia=f"torcida:{convite.torcida_id}")
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
        return Response({"mensagem":"Convite revogado."})

class DetalheMembroView(APIView):
    permission_classes = [IsAuthenticated]
    def obter_membro(self,torcida,membro_id):
        return get_object_or_404(Membro.objects.select_related("usuario").filter(torcida=torcida),pk=membro_id)
    def patch(self,request,torcida_id,membro_id):
        torcida=obter_torcida(request,torcida_id); exigir_admin(request,torcida); membro=self.obter_membro(torcida,membro_id)
        if membro.papel == Membro.Papel.ADMIN: raise ValidationError("A transferência de administração exige procedimento específico.")
        papel=request.data.get("papel")
        if papel not in (Membro.Papel.MEMBRO,Membro.Papel.MODERADOR): raise ValidationError({"papel":"Use membro ou moderador."})
        membro.papel=papel; membro.save(update_fields=["papel"]); return Response(MembroSerializer(membro).data)
    def delete(self,request,torcida_id,membro_id):
        torcida=obter_torcida(request,torcida_id); exigir_admin(request,torcida); membro=self.obter_membro(torcida,membro_id)
        if membro.papel == Membro.Papel.ADMIN: raise ValidationError("Não é permitido remover um administrador por este endpoint.")
        membro.delete(); return Response(status=status.HTTP_204_NO_CONTENT)
