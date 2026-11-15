import os
from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from accounts.permissions import is_platform_admin
from torcidas.models import Membro
from .models import Evento, IngressoEvento
from store.payments import MercadoPagoError, create_event_ticket_preference
from .serializers import EventoSerializer


class EventoViewSet(viewsets.ModelViewSet):
    serializer_class = EventoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Evento.objects.select_related("torcida", "criado_por")
        if is_platform_admin(self.request.user):
            return queryset
        usuario = self.request.user
        torcidas_gerenciadas = Membro.objects.filter(
            usuario=usuario,
            papel__in=[Membro.Papel.ADMIN, Membro.Papel.MODERADOR],
        ).values("torcida_id")
        torcidas_membro = Membro.objects.filter(
            usuario=usuario,
        ).values("torcida_id")
        return queryset.filter(
            Q(torcida_id__in=torcidas_gerenciadas)
            | Q(
                torcida_id__in=torcidas_membro,
                status__in=[Evento.Status.PUBLICADO, Evento.Status.ENCERRADO],
            )
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(criado_por=self.request.user)

    def perform_update(self, serializer):
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        evento = self.get_object()
        if not is_platform_admin(request.user):
            gerente = Membro.objects.filter(
                torcida=evento.torcida,
                usuario=request.user,
                papel__in=[Membro.Papel.ADMIN, Membro.Papel.MODERADOR],
            ).exists()
            if not gerente:
                raise PermissionDenied("Somente administradores e moderadores podem excluir eventos.")
        evento.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class IngressoEventoView(APIView):
    permission_classes = [IsAuthenticated]

    def _evento(self, request, evento_id):
        evento = get_object_or_404(Evento, pk=evento_id, status=Evento.Status.PUBLICADO)
        if not Membro.objects.filter(usuario=request.user, torcida_id=evento.torcida_id).exists() and not is_platform_admin(request.user):
            raise PermissionDenied("Você precisa participar desta torcida para comprar ingresso.")
        return evento

    def get(self, request, evento_id):
        evento = self._evento(request, evento_id)
        ingressos = IngressoEvento.objects.filter(evento=evento, comprador=request.user).order_by("-criado_em")
        data = [{"id": i.id, "codigo": str(i.codigo), "quantidade": i.quantidade, "valor_total": str(i.valor_total), "status": i.status, "checkout_url": i.checkout_url, "criado_em": i.criado_em} for i in ingressos]
        return Response({"ingressos": data, "pode_entrar": ingressos.filter(status=IngressoEvento.Status.PAGO).exists()})

    def post(self, request, evento_id):
        evento = self._evento(request, evento_id)
        try:
            quantidade = int(request.data.get("quantidade", 1))
        except (TypeError, ValueError):
            return Response({"detail": "Quantidade inválida."}, status=400)
        if quantidade < 1 or quantidade > 6:
            return Response({"detail": "Você pode comprar de 1 a 6 ingressos por pedido."}, status=400)
        metodo = str(request.data.get("metodo_pagamento", "pix")).lower()
        if metodo not in ("pix", "cartao", "boleto"):
            return Response({"detail": "Escolha Pix, cartão ou boleto."}, status=400)
        with transaction.atomic():
            locked = Evento.objects.select_for_update().get(pk=evento.pk)
            if locked.status != Evento.Status.PUBLICADO or locked.inicio_em <= timezone.now():
                return Response({"detail": "As vendas deste evento estão encerradas."}, status=409)
            if locked.capacidade:
                ocupadas = IngressoEvento.objects.filter(evento=locked).filter(
                    Q(status=IngressoEvento.Status.PAGO) |
                    Q(status=IngressoEvento.Status.AGUARDANDO, expira_em__gt=timezone.now())
                ).aggregate(total=Sum("quantidade"))["total"] or 0
                if ocupadas + quantidade > locked.capacidade:
                    return Response({"detail": "Não há ingressos suficientes para essa quantidade."}, status=409)
            total = (locked.valor * quantidade).quantize(Decimal("0.01"))
            if total == 0:
                ingresso = IngressoEvento.objects.create(evento=locked, comprador=request.user, quantidade=quantidade, valor_total=total, status=IngressoEvento.Status.PAGO)
                return Response({"status": ingresso.status, "codigo": str(ingresso.codigo), "quantidade": quantidade, "valor_total": str(total)}, status=201)
            if not request.user.email:
                return Response({"detail": "Adicione um e-mail válido ao seu cadastro antes de comprar."}, status=400)
            ingresso = IngressoEvento.objects.create(evento=locked, comprador=request.user, quantidade=quantidade, valor_total=total, metodo_pagamento=metodo, expira_em=timezone.now() + timedelta(minutes=30))
        frontend_url = os.getenv("TORCIDA_FRONTEND_URL", "").strip()
        if not frontend_url:
            ingresso.delete()
            return Response({"detail": "Checkout indisponível: configure TORCIDA_FRONTEND_URL no servidor."}, status=503)
        try:
            preference = create_event_ticket_preference(ingresso, metodo, frontend_url)
        except MercadoPagoError as exc:
            ingresso.delete()
            return Response({"detail": str(exc)}, status=503)
        ingresso.preference_id = str(preference.get("id", ""))
        ingresso.checkout_url = preference.get("init_point") or preference.get("sandbox_init_point") or ""
        if not ingresso.checkout_url:
            ingresso.delete()
            return Response({"detail": "O provedor não retornou o endereço de pagamento."}, status=502)
        ingresso.save(update_fields=["preference_id", "checkout_url"])
        return Response({"status": ingresso.status, "checkout_url": ingresso.checkout_url, "quantidade": quantidade, "valor_total": str(total)}, status=201)
