from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from store.models import Pedido
from store.payments import MercadoPagoError, search_order_payments
from store.views import cancelar_pedido_e_devolver_estoque


class Command(BaseCommand):
    help = "Reconcilia pagamentos e libera reservas de pedidos vencidos."

    def handle(self, *args, **options):
        now = timezone.now()
        cutoff = now - timedelta(minutes=30)
        candidates = Pedido.objects.filter(
            status=Pedido.Status.AGUARDANDO,
            status_pagamento__in=("nao_iniciado", "pending", "in_process"),
        ).filter(
            Q(expira_em__lte=now)
            | Q(expira_em__isnull=True, criado_em__lte=cutoff)
        ).values_list("id", flat=True)

        cancelados = 0
        confirmados = 0
        mantidos = 0
        falhas = 0

        for pedido_id in candidates.iterator():
            try:
                resultado = search_order_payments(pedido_id)
            except MercadoPagoError as exc:
                falhas += 1
                self.stderr.write(f"Pedido #{pedido_id}: consulta ao Mercado Pago falhou: {exc}")
                continue

            pagamentos = resultado.get("results") or []
            status_pagamentos = {str(item.get("status", "")).lower() for item in pagamentos}

            if "approved" in status_pagamentos:
                pagamento = next(item for item in pagamentos if str(item.get("status", "")).lower() == "approved")
                with transaction.atomic():
                    pedido = Pedido.objects.select_for_update().filter(
                        pk=pedido_id, status=Pedido.Status.AGUARDANDO
                    ).first()
                    if pedido:
                        pedido.status = Pedido.Status.PAGO
                        pedido.status_pagamento = "approved"
                        pedido.mercado_pago_payment_id = str(pagamento.get("id", ""))
                        pedido.save(update_fields=[
                            "status", "status_pagamento", "mercado_pago_payment_id"
                        ])
                        confirmados += 1
                continue

            # Só libera estoque se o provedor confirmar que não existe pagamento
            # ou que todas as tentativas encontradas terminaram sem aprovação.
            terminais_sem_pagamento = {"cancelled", "rejected", "refunded", "charged_back"}
            if pagamentos and not status_pagamentos.issubset(terminais_sem_pagamento):
                mantidos += 1
                continue

            with transaction.atomic():
                pedido = Pedido.objects.select_for_update().filter(
                    pk=pedido_id,
                    status=Pedido.Status.AGUARDANDO,
                    estoque_devolvido=False,
                ).first()
                if not pedido:
                    continue
                cancelar_pedido_e_devolver_estoque(pedido)
                if pagamentos:
                    pedido.status_pagamento = next(iter(status_pagamentos), "cancelled")
                    pedido.save(update_fields=["status_pagamento"])
                cancelados += 1

        self.stdout.write(self.style.SUCCESS(
            f"Expiração concluída: {cancelados} cancelados/liberados, "
            f"{confirmados} pagamentos confirmados, {mantidos} aguardando provedor, "
            f"{falhas} falhas de consulta."
        ))
