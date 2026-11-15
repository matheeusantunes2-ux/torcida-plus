import secrets
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from django.core import signing
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import is_platform_admin
from .models import Torcida, Membro, PlanoAssociacao, Associacao
from .audit_views import registrar_atividade

QR_SALT = "torcida-plus-membership-qr-v1"
QR_MAX_AGE = 90

def _torcida_visivel(request, torcida_id):
    qs = Torcida.objects.filter(pk=torcida_id)
    if is_platform_admin(request.user):
        return get_object_or_404(qs)
    return get_object_or_404(qs.filter(membros__usuario=request.user).distinct())

def _exigir_gestor(request, torcida):
    if is_platform_admin(request.user):
        return
    if not Membro.objects.filter(torcida=torcida, usuario=request.user, papel=Membro.Papel.ADMIN).exists():
        raise PermissionDenied("Somente a administração da torcida pode executar esta ação.")

class PlanosAssociacaoView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        # A consulta pública de planos não expõe dados pessoais; a gestão exige login.
        if self.request.method == "GET":
            return [AllowAny()]
        return [permission() for permission in self.permission_classes]
    def get(self, request, torcida_id):
        torcida = get_object_or_404(Torcida, pk=torcida_id)
        planos = PlanoAssociacao.objects.filter(torcida=torcida, ativo=True).order_by("valor", "nome")
        return Response([{"id":p.id,"nome":p.nome,"descricao":p.descricao,"valor":str(p.valor),"duracao_dias":p.duracao_dias} for p in planos])
    def post(self, request, torcida_id):
        torcida = _torcida_visivel(request, torcida_id); _exigir_gestor(request, torcida)
        nome = str(request.data.get("nome", "")).strip(); descricao = str(request.data.get("descricao", "")).strip()
        try:
            valor = Decimal(str(request.data.get("valor", "0"))); dias = int(request.data.get("duracao_dias", 365))
        except (ValueError, TypeError, InvalidOperation):
            raise ValidationError("Informe valor e duração válidos.")
        if not nome or len(nome)>100 or len(descricao)>300 or not valor.is_finite() or valor<0 or valor>99999999 or not 1<=dias<=3650:
            raise ValidationError("Plano inválido. Confira nome, descrição, valor e duração (1 a 3650 dias).")
        try:
            plano=PlanoAssociacao.objects.create(torcida=torcida,nome=nome,descricao=descricao,valor=valor,duracao_dias=dias)
        except IntegrityError:
            raise ValidationError({"nome":"Já existe um plano com esse nome nesta torcida."})
        return Response({"id":plano.id,"nome":plano.nome,"valor":str(plano.valor),"duracao_dias":plano.duracao_dias},status=status.HTTP_201_CREATED)

class SolicitarAssociacaoView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, torcida_id):
        torcida=get_object_or_404(Torcida,pk=torcida_id); plano=get_object_or_404(PlanoAssociacao,pk=request.data.get("plano_id"),torcida=torcida,ativo=True)
        if Associacao.objects.filter(torcida=torcida,usuario=request.user).exclude(status=Associacao.Status.CANCELADA).exists():
            raise ValidationError("Você já possui uma solicitação ou associação nesta torcida.")
        a=Associacao.objects.create(torcida=torcida,usuario=request.user,plano=plano)
        return Response({"id":a.id,"status":a.status,"plano":plano.nome,"valor":str(plano.valor),"mensagem":"Solicitação registrada. A diretoria confirmará a associação."},status=status.HTTP_201_CREATED)

class MinhasAssociacoesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        qs=Associacao.objects.filter(usuario=request.user).select_related("torcida","plano")
        return Response([{"id":a.id,"torcida":a.torcida.nome,"torcida_id":a.torcida_id,"plano":a.plano.nome,"valor":str(a.plano.valor),"status":a.status,"inicio_em":a.inicio_em,"fim_em":a.fim_em} for a in qs])

class GestaoAssociacoesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, torcida_id):
        torcida=_torcida_visivel(request,torcida_id); _exigir_gestor(request,torcida)
        qs=Associacao.objects.filter(torcida=torcida).select_related("usuario","plano").order_by("-criado_em")
        return Response([{"id":a.id,"usuario_id":a.usuario_id,"username":a.usuario.get_username(),"plano":a.plano.nome,"valor":str(a.plano.valor),"status":a.status,"criado_em":a.criado_em} for a in qs])
    def patch(self, request, torcida_id, associacao_id):
        torcida=_torcida_visivel(request,torcida_id); _exigir_gestor(request,torcida)
        with transaction.atomic():
            a=get_object_or_404(Associacao.objects.select_for_update(),pk=associacao_id,torcida=torcida); novo=request.data.get("status")
            if novo==Associacao.Status.ATIVA:
                if a.plano.valor>0 and request.data.get("confirmacao_pagamento") is not True:
                    raise ValidationError("Para plano pago, confirme manualmente que o pagamento foi recebido antes de ativar.")
                agora=timezone.now(); a.status=Associacao.Status.ATIVA; a.inicio_em=agora; a.fim_em=agora+timedelta(days=a.plano.duracao_dias); a.aprovado_por=request.user
                Membro.objects.get_or_create(usuario=a.usuario,torcida=torcida,defaults={"papel":Membro.Papel.MEMBRO})
            elif novo in (Associacao.Status.CANCELADA,Associacao.Status.PENDENTE): a.status=novo
            else: raise ValidationError({"status":"Use ativa, pendente ou cancelada."})
            a.save()
        return Response({"id":a.id,"status":a.status,"inicio_em":a.inicio_em,"fim_em":a.fim_em})

class CarteirinhaQRView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self,request,associacao_id):
        a=get_object_or_404(Associacao.objects.select_related("torcida"),pk=associacao_id,usuario=request.user,status=Associacao.Status.ATIVA)
        if not a.fim_em or a.fim_em<=timezone.now(): raise ValidationError("Associação expirada.")
        payload=f"{a.id}:{a.torcida_id}:{secrets.token_urlsafe(12)}"
        token=signing.TimestampSigner(salt=QR_SALT).sign(payload)
        return Response({"qr_token":token,"validade_segundos":QR_MAX_AGE,"associacao_id":a.id,"torcida":a.torcida.nome})

class ValidarCarteirinhaQRView(APIView):
    permission_classes=[IsAuthenticated]
    def post(self,request,torcida_id):
        torcida=_torcida_visivel(request,torcida_id); _exigir_gestor(request,torcida); token=request.data.get("qr_token","")
        if not isinstance(token,str) or len(token)>500: raise ValidationError("QR inválido.")
        try:
            raw=signing.TimestampSigner(salt=QR_SALT).unsign(token,max_age=QR_MAX_AGE); assoc_id,tenant_id,nonce=raw.split(":",2)
            if int(tenant_id)!=torcida.id: raise signing.BadSignature("tenant")
            a=Associacao.objects.select_related("usuario","plano").get(pk=int(assoc_id),torcida=torcida,status=Associacao.Status.ATIVA)
            if not a.fim_em or a.fim_em<=timezone.now(): raise signing.BadSignature("expired membership")
        except (signing.BadSignature,ValueError,Associacao.DoesNotExist):
            registrar_atividade(torcida,request.user,"validacao_qr_falha","Tentativa de validação de carteirinha recusada.")
            return Response({"valido":False,"mensagem":"Carteirinha inválida, expirada ou de outra torcida."})
        registrar_atividade(torcida,request.user,"validacao_qr_sucesso",f"Carteirinha validada para associação #{a.id}.")
        return Response({"valido":True,"associado":a.usuario.get_username(),"plano":a.plano.nome,"validade":a.fim_em})
