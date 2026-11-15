import secrets
from datetime import date, timedelta
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
from .models import Torcida, Membro, PlanoAssociacao, Associacao, PagamentoAssociacao
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


class PagamentosAssociacaoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, torcida_id):
        torcida = _torcida_visivel(request, torcida_id)
        _exigir_gestor(request, torcida)
        hoje = timezone.localdate()
        PagamentoAssociacao.objects.filter(associacao__torcida=torcida, status=PagamentoAssociacao.Status.PENDENTE, vencimento__lt=hoje).update(status=PagamentoAssociacao.Status.ATRASADO)
        qs = PagamentoAssociacao.objects.filter(associacao__torcida=torcida).select_related("associacao__usuario", "associacao__plano", "confirmado_por").order_by("vencimento", "id")
        return Response([{
            "id": p.id, "associacao_id": p.associacao_id,
            "username": p.associacao.usuario.get_username(),
            "plano": p.associacao.plano.nome,
            "valor": str(p.valor), "vencimento": p.vencimento,
            "status": p.status, "pago_em": p.pago_em,
            "confirmado_por": p.confirmado_por.get_username() if p.confirmado_por else None,
            "observacao": p.observacao,
        } for p in qs])

    def post(self, request, torcida_id):
        torcida = _torcida_visivel(request, torcida_id)
        _exigir_gestor(request, torcida)
        try:
            associacao = Associacao.objects.select_related("plano").get(pk=request.data.get("associacao_id"), torcida=torcida)
            valor = Decimal(str(request.data.get("valor", associacao.plano.valor)))
            vencimento = date.fromisoformat(str(request.data.get("vencimento", "")))
        except (Associacao.DoesNotExist, ValueError, TypeError, InvalidOperation):
            raise ValidationError("Informe uma associação existente, valor e vencimento válidos.")
        if associacao.status == Associacao.Status.CANCELADA:
            raise ValidationError("Não é possível gerar cobrança para uma associação cancelada.")
        observacao = str(request.data.get("observacao", "")).strip()
        if not valor.is_finite() or valor <= 0 or valor > Decimal("99999999") or len(observacao) > 240:
            raise ValidationError("Valor ou observação inválidos.")
        try:
            pagamento = PagamentoAssociacao.objects.create(associacao=associacao, valor=valor, vencimento=vencimento, observacao=observacao)
        except IntegrityError:
            raise ValidationError("Já existe uma cobrança para esta associação nesta data de vencimento.")
        registrar_atividade(torcida, request.user, "cobranca_criada", f"Cobrança #{pagamento.id} criada para associação #{associacao.id}, vencimento {vencimento}.")
        return Response({"id": pagamento.id, "status": pagamento.status, "valor": str(pagamento.valor), "vencimento": pagamento.vencimento}, status=status.HTTP_201_CREATED)


class DetalhePagamentoAssociacaoView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, torcida_id, pagamento_id):
        torcida = _torcida_visivel(request, torcida_id)
        _exigir_gestor(request, torcida)
        with transaction.atomic():
            pagamento = get_object_or_404(PagamentoAssociacao.objects.select_for_update().select_related("associacao__plano"), pk=pagamento_id, associacao__torcida=torcida)
            novo = request.data.get("status")
            if novo == PagamentoAssociacao.Status.PAGO:
                if pagamento.status == PagamentoAssociacao.Status.CANCELADO:
                    raise ValidationError("Uma cobrança cancelada não pode ser recebida.")
                if pagamento.status != PagamentoAssociacao.Status.PAGO:
                    associacao = Associacao.objects.select_for_update().get(pk=pagamento.associacao_id)
                    if associacao.status == Associacao.Status.CANCELADA:
                        raise ValidationError("A associação foi cancelada e não pode ser renovada por esta cobrança.")
                    agora = timezone.now()
                    base = associacao.fim_em if associacao.fim_em and associacao.fim_em > agora else agora
                    associacao.status = Associacao.Status.ATIVA
                    associacao.inicio_em = associacao.inicio_em or agora
                    associacao.fim_em = base + timedelta(days=associacao.plano.duracao_dias)
                    associacao.aprovado_por = request.user
                    associacao.save(update_fields=["status", "inicio_em", "fim_em", "aprovado_por", "atualizado_em"])
                    Membro.objects.get_or_create(usuario=associacao.usuario, torcida=torcida, defaults={"papel": Membro.Papel.MEMBRO})
                    pagamento.status = PagamentoAssociacao.Status.PAGO
                    pagamento.pago_em = agora
                    pagamento.confirmado_por = request.user
                    pagamento.save(update_fields=["status", "pago_em", "confirmado_por"])
                    registrar_atividade(torcida, request.user, "pagamento_confirmado", f"Pagamento #{pagamento.id} confirmado; associação #{associacao.id} ativada/renovada.")
            elif novo == PagamentoAssociacao.Status.CANCELADO:
                if pagamento.status == PagamentoAssociacao.Status.PAGO:
                    raise ValidationError("Pagamento confirmado não pode ser cancelado por esta operação.")
                pagamento.status = PagamentoAssociacao.Status.CANCELADO
                pagamento.save(update_fields=["status"])
                registrar_atividade(torcida, request.user, "cobranca_cancelada", f"Cobrança #{pagamento.id} cancelada.")
            else:
                raise ValidationError({"status": "Use pago ou cancelado."})
        return Response({"id": pagamento.id, "status": pagamento.status, "pago_em": pagamento.pago_em})
