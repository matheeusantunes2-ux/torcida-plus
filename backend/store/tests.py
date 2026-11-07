from decimal import Decimal
import hashlib
import hmac
import time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from store.models import ItemCarrinho, ItemPedido, Pedido, Produto
from store.payments import validate_webhook_signature
from torcidas.models import Membro, Torcida


class StoreFlowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(username="admin-loja", password="test-password-123")
        self.member = User.objects.create_user(username="membro-loja", password="test-password-123")
        self.torcida = Torcida.objects.create(nome="Torcida Teste", slug="torcida-teste")
        Membro.objects.create(usuario=self.admin, torcida=self.torcida, papel="admin")
        Membro.objects.create(usuario=self.member, torcida=self.torcida, papel="membro")
        self.client = APIClient()
        self.client.force_authenticate(self.member)
        self.produto = Produto.objects.create(
            torcida=self.torcida, nome="Camisa teste", descricao="Produto para testes",
            categoria="Vestuário", preco=Decimal("79.90"), quantidade=3,
        )
        self.endereco = {
            "torcida": self.torcida.id, "nome_destinatario": "Pessoa Teste",
            "telefone": "21999990000", "cep": "20000000", "endereco": "Rua de Teste",
            "numero": "10", "bairro": "Centro", "cidade": "Rio de Janeiro", "uf": "RJ",
        }

    def test_carrinho_preserva_item_quando_quantidade_excede_estoque(self):
        response = self.client.post("/api/loja/carrinho/", {"produto_id": self.produto.id, "quantidade": 2}, format="json")
        self.assertEqual(response.status_code, 201)
        excedente = self.client.post("/api/loja/carrinho/", {"produto_id": self.produto.id, "quantidade": 2}, format="json")
        self.assertEqual(excedente.status_code, 400)
        self.assertIn("mantido sem alterações", excedente.data["detail"])
        item = ItemCarrinho.objects.get(usuario=self.member, produto=self.produto)
        self.assertEqual(item.quantidade, 2)

    def test_checkout_cria_pedido_e_baixa_estoque_atomicamente(self):
        ItemCarrinho.objects.create(usuario=self.member, produto=self.produto, quantidade=2)
        response = self.client.post("/api/loja/checkout/", self.endereco, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], Pedido.Status.AGUARDANDO)
        self.assertEqual(Decimal(response.data["total"]), Decimal("159.80"))
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 1)
        self.assertEqual(ItemPedido.objects.filter(pedido_id=response.data["id"]).count(), 1)
        self.assertFalse(ItemCarrinho.objects.filter(usuario=self.member, produto=self.produto).exists())

    def test_checkout_sem_estoque_nao_cria_pedido_nem_remove_carrinho(self):
        ItemCarrinho.objects.create(usuario=self.member, produto=self.produto, quantidade=4)
        response = self.client.post("/api/loja/checkout/", self.endereco, format="json")
        self.assertEqual(response.status_code, 409)
        self.assertFalse(Pedido.objects.exists())
        self.assertTrue(ItemCarrinho.objects.filter(usuario=self.member, produto=self.produto).exists())
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 3)

    def test_membro_comum_nao_pode_cadastrar_produto(self):
        response = self.client.post("/api/loja/produtos/", {
            "torcida": self.torcida.id, "nome": "Produto indevido", "preco": "10.00", "quantidade": 1,
        }, format="json")
        self.assertEqual(response.status_code, 403)


    def test_pagamento_nao_expoe_checkout_de_pedido_de_outro_usuario(self):
        pedido = Pedido.objects.create(
            torcida=self.torcida, comprador=self.admin, total=Decimal("79.90"),
            nome_destinatario="Admin", telefone="21999990000", cep="20000000",
            endereco="Rua de Teste", numero="10", bairro="Centro",
            cidade="Rio de Janeiro", uf="RJ",
        )
        response = self.client.post(
            f"/api/loja/pedidos/{pedido.id}/pagar/",
            {"metodo_pagamento": "pix"}, format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_pagamento_exige_metodo_valido(self):
        pedido = Pedido.objects.create(
            torcida=self.torcida, comprador=self.member, total=Decimal("79.90"),
            nome_destinatario="Pessoa Teste", telefone="21999990000", cep="20000000",
            endereco="Rua de Teste", numero="10", bairro="Centro",
            cidade="Rio de Janeiro", uf="RJ",
        )
        response = self.client.post(
            f"/api/loja/pedidos/{pedido.id}/pagar/",
            {"metodo_pagamento": "dinheiro"}, format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch.dict("os.environ", {"TORCIDA_FRONTEND_URL": "https://torcida.example"})
    def test_pagamento_informa_quando_gateway_nao_esta_configurado(self):
        self.member.email = "member@example.com"
        self.member.save(update_fields=["email"])
        pedido = Pedido.objects.create(
            torcida=self.torcida, comprador=self.member, total=Decimal("79.90"),
            nome_destinatario="Pessoa Teste", telefone="21999990000", cep="20000000",
            endereco="Rua de Teste", numero="10", bairro="Centro",
            cidade="Rio de Janeiro", uf="RJ",
        )
        with patch.dict("os.environ", {"MERCADO_PAGO_ACCESS_TOKEN": ""}):
            response = self.client.post(
                f"/api/loja/pedidos/{pedido.id}/pagar/",
                {"metodo_pagamento": "pix"}, format="json",
            )
        self.assertEqual(response.status_code, 503)
        self.assertIn("MERCADO_PAGO_ACCESS_TOKEN", response.data["detail"])

    def test_admin_pode_carregar_dez_produtos_demo(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/loja/catalogo-demo/", {"torcida": self.torcida.id}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Produto.objects.filter(torcida=self.torcida, ativo=True).count(), 11)
        self.assertEqual(response.data["total"], 10)



class MercadoPagoWebhookSignatureTests(TestCase):
    def _signature(self, secret, data_id, request_id, timestamp):
        manifest = f"id:{data_id.lower()};request-id:{request_id};ts:{timestamp};"
        digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
        return f"ts={timestamp},v1={digest}"

    @patch.dict("os.environ", {"MERCADO_PAGO_WEBHOOK_SECRET": "segredo-de-teste"})
    def test_assinatura_webhook_valida_e_aceita_timestamp_em_segundos(self):
        ts = str(int(time.time()))
        signature = self._signature("segredo-de-teste", "123456", "request-abc", ts)
        self.assertTrue(validate_webhook_signature(signature, "request-abc", "123456"))

    @patch.dict("os.environ", {"MERCADO_PAGO_WEBHOOK_SECRET": "segredo-de-teste"})
    def test_assinatura_webhook_rejeita_hash_alterado(self):
        ts = str(int(time.time()))
        signature = self._signature("segredo-de-teste", "123456", "request-abc", ts)
        self.assertFalse(validate_webhook_signature(signature, "request-abc", "654321"))

    @patch.dict("os.environ", {"MERCADO_PAGO_WEBHOOK_SECRET": "segredo-de-teste"})
    def test_assinatura_webhook_rejeita_timestamp_antigo(self):
        ts = str(int(time.time()) - 600)
        signature = self._signature("segredo-de-teste", "123456", "request-abc", ts)
        self.assertFalse(validate_webhook_signature(signature, "request-abc", "123456"))

def test_superuser_global_pode_gerenciar_loja_sem_ser_membro(self):
        global_admin = get_user_model().objects.create_superuser(
            username="platform_admin_store", email="", password="Strong-Test-Password-2026!"
        )
        self.client.force_authenticate(global_admin)
        response = self.client.get(
            "/api/loja/produtos/", {"torcida": self.torcida.pk}
        )
        self.assertEqual(response.status_code, 200)
        cadastro = self.client.post("/api/loja/produtos/", {
            "torcida": self.torcida.pk,
            "nome": "Produto administrador global",
            "descricao": "Produto criado pelo administrador da plataforma",
            "categoria": "Acessórios",
            "preco": "19.90",
            "quantidade": 5,
        }, format="json")
        self.assertEqual(cadastro.status_code, 201)
