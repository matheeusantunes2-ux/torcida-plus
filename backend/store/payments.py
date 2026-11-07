"""Integração segura com Mercado Pago Checkout Pro (Preferences API)."""
import hashlib
import hmac
import json
import os
import time
import urllib.error
import urllib.request
from uuid import uuid4


API_BASE = "https://api.mercadopago.com"


class MercadoPagoError(Exception):
    pass


def _request(path, method="GET", payload=None, idempotency_key=None):
    token = os.getenv("MERCADO_PAGO_ACCESS_TOKEN", "").strip()
    if not token:
        raise MercadoPagoError("Pagamentos ainda não configurados. Configure MERCADO_PAGO_ACCESS_TOKEN no servidor.")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    if payload is not None:
        headers["Content-Type"] = "application/json"
    if idempotency_key:
        headers["X-Idempotency-Key"] = idempotency_key
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(API_BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise MercadoPagoError(f"Mercado Pago recusou a operação (HTTP {exc.code}): {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise MercadoPagoError("Não foi possível conectar ao Mercado Pago. Tente novamente.") from exc


def create_preference(order, method, frontend_url):
    allowed = {"pix", "cartao", "boleto"}
    if method not in allowed:
        raise MercadoPagoError("Método de pagamento inválido.")
    if not order.comprador.email:
        raise MercadoPagoError("Adicione um e-mail válido ao seu cadastro antes de pagar.")
    excluded = {
        "pix": ["credit_card", "debit_card", "ticket", "atm", "prepaid_card"],
        "cartao": ["ticket", "bank_transfer", "atm"],
        "boleto": ["credit_card", "debit_card", "bank_transfer", "atm", "prepaid_card"],
    }[method]
    items = [
        {
            "id": str(item.produto_id),
            "title": item.nome_produto[:256],
            "description": f"Pedido TORCIDA+ #{order.id}",
            "quantity": item.quantidade,
            "currency_id": "BRL",
            "unit_price": float(item.preco_unitario),
        }
        for item in order.itens.all()
    ]
    base = frontend_url.rstrip("/")
    payload = {
        "items": items,
        "payer": {"email": order.comprador.email},
        "external_reference": f"torcida-plus-order-{order.id}",
        "statement_descriptor": "TORCIDA MAIS",
        "payment_methods": {"excluded_payment_types": [{"id": value} for value in excluded]},
        "back_urls": {
            "success": f"{base}/?store_payment=success&order_id={order.id}",
            "pending": f"{base}/?store_payment=pending&order_id={order.id}",
            "failure": f"{base}/?store_payment=failure&order_id={order.id}",
        },
        "auto_return": "approved",
        "notification_url": os.getenv("MERCADO_PAGO_WEBHOOK_URL", "").strip() or None,
        "metadata": {"torcida_plus_order_id": order.id},
    }
    payload = {key: value for key, value in payload.items() if value is not None}
    return _request("/checkout/preferences", method="POST", payload=payload, idempotency_key=str(uuid4()))


def get_payment(payment_id):
    return _request(f"/v1/payments/{payment_id}")


def validate_webhook_signature(signature, request_id, data_id):
    secret = os.getenv("MERCADO_PAGO_WEBHOOK_SECRET", "").strip()
    if not secret or not signature or not request_id or not data_id:
        return False
    parts = {}
    for entry in signature.split(","):
        if "=" in entry:
            key, value = entry.strip().split("=", 1)
            parts[key] = value
    ts, received = parts.get("ts"), parts.get("v1")
    if not ts or not received:
        return False
    try:
        if abs(int(time.time()) - int(ts) // 1000) > 300:
            return False
    except ValueError:
        return False
    manifest = f"id:{str(data_id).lower()};request-id:{request_id};ts:{ts};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)
