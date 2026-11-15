from decimal import Decimal
import hashlib
import hmac
import time
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from django.core.files.uploadedfile import SimpleUploadedFile

from store.models import ItemCarrinho, ItemPedido, Pedido, Produto, MovimentacaoEstoque
from store.payments import validate_webhook_signature
from store.serializers import ProdutoSerializer
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

    def test_checkout_registra_reserva_e_cancelamento_registra_devolucao(self):
        ItemCarrinho.objects.create(usuario=self.member, produto=self.produto, quantidade=2)
        checkout = self.client.post("/api/loja/checkout/", self.endereco, format="json")
        pedido_id = checkout.data["id"]
        reserva = MovimentacaoEstoque.objects.get(
            pedido_id=pedido_id, produto=self.produto,
            tipo=MovimentacaoEstoque.Tipo.RESERVA,
        )
        self.assertEqual(reserva.quantidade, 2)
        self.assertEqual(reserva.saldo_anterior, 3)
        self.assertEqual(reserva.saldo_posterior, 1)

        self.client.force_authenticate(self.admin)
        cancelamento = self.client.patch(
            f"/api/loja/pedidos/{pedido_id}/",
            {"status": Pedido.Status.CANCELADO}, format="json",
        )
        self.assertEqual(cancelamento.status_code, 200)
        devolucao = MovimentacaoEstoque.objects.get(
            pedido_id=pedido_id, produto=self.produto,
            tipo=MovimentacaoEstoque.Tipo.DEVOLUCAO,
        )
        self.assertEqual(devolucao.quantidade, 2)
        self.assertEqual(devolucao.saldo_anterior, 1)
        self.assertEqual(devolucao.saldo_posterior, 3)
        self.assertEqual(MovimentacaoEstoque.objects.filter(pedido_id=pedido_id).count(), 2)

    def test_historico_de_estoque_restrito_ao_admin_global(self):
        ItemCarrinho.objects.create(usuario=self.member, produto=self.produto, quantidade=1)
        self.client.post("/api/loja/checkout/", self.endereco, format="json")
        response_membro = self.client.get("/api/loja/estoque/movimentacoes/")
        self.assertEqual(response_membro.status_code, 403)
        self.admin.is_superuser = True
        self.admin.save(update_fields=["is_superuser"])
        self.client.force_authenticate(self.admin)
        response_admin = self.client.get("/api/loja/estoque/movimentacoes/")
        self.assertEqual(response_admin.status_code, 200)
        self.assertEqual(len(response_admin.data["results"]), 1)
        self.assertEqual(response_admin.data["results"][0]["tipo"], "reserva")

    def test_checkout_sem_estoque_nao_cria_pedido_nem_remove_carrinho(self):
        ItemCarrinho.objects.create(usuario=self.member, produto=self.produto, quantidade=4)
        response = self.client.post("/api/loja/checkout/", self.endereco, format="json")
        self.assertEqual(response.status_code, 409)
        self.assertFalse(Pedido.objects.exists())
        self.assertTrue(ItemCarrinho.objects.filter(usuario=self.member, produto=self.produto).exists())
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 3)



    def test_cancelamento_de_pedido_devolve_estoque_uma_unica_vez(self):
        ItemCarrinho.objects.create(usuario=self.member, produto=self.produto, quantidade=2)
        checkout = self.client.post("/api/loja/checkout/", self.endereco, format="json")
        self.assertEqual(checkout.status_code, 201)
        pedido_id = checkout.data["id"]
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 1)

        self.client.force_authenticate(self.admin)
        cancelamento = self.client.patch(
            f"/api/loja/pedidos/{pedido_id}/",
            {"status": Pedido.Status.CANCELADO}, format="json",
        )
        self.assertEqual(cancelamento.status_code, 200)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 3)
        pedido = Pedido.objects.get(pk=pedido_id)
        self.assertTrue(pedido.estoque_devolvido)

        repetido = self.client.patch(
            f"/api/loja/pedidos/{pedido_id}/",
            {"status": Pedido.Status.CANCELADO}, format="json",
        )
        self.assertEqual(repetido.status_code, 200)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 3)

    def test_pedido_pago_nao_pode_ser_cancelado_sem_estorno(self):
        ItemCarrinho.objects.create(usuario=self.member, produto=self.produto, quantidade=1)
        checkout = self.client.post("/api/loja/checkout/", self.endereco, format="json")
        pedido_id = checkout.data["id"]
        pedido = Pedido.objects.get(pk=pedido_id)
        pedido.status_pagamento = "approved"
        pedido.status = Pedido.Status.PAGO
        pedido.save(update_fields=["status_pagamento", "status"])
        self.client.force_authenticate(self.admin)
        response = self.client.patch(
            f"/api/loja/pedidos/{pedido_id}/",
            {"status": Pedido.Status.CANCELADO}, format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 2)
        pedido.refresh_from_db()
        self.assertFalse(pedido.estoque_devolvido)

    def _criar_pedido_expirado(self, status_pagamento="nao_iniciado"):
        ItemCarrinho.objects.create(usuario=self.member, produto=self.produto, quantidade=1)
        response = self.client.post("/api/loja/checkout/", self.endereco, format="json")
        pedido = Pedido.objects.get(pk=response.data["id"])
        pedido.expira_em = timezone.now() - timedelta(minutes=1)
        pedido.status_pagamento = status_pagamento
        pedido.save(update_fields=["expira_em", "status_pagamento"])
        return pedido

    @patch("store.management.commands.expirar_pedidos.search_order_payments", return_value={"results": []})
    def test_rotina_expira_pedido_sem_pagamento_e_libera_estoque(self, _search):
        pedido = self._criar_pedido_expirado()
        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade, 2)
        call_command("expirar_pedidos")
        pedido.refresh_from_db()
        self.produto.refresh_from_db()
        self.assertEqual(pedido.status, Pedido.Status.CANCELADO)
        self.assertTrue(pedido.estoque_devolvido)
        self.assertEqual(self.produto.quantidade, 3)

    @patch("store.management.commands.expirar_pedidos.search_order_payments", return_value={"results": [{"id": "mp-123", "status": "approved"}]})
    def test_rotina_reconcilia_pagamento_aprovado_antes_de_cancelar(self, _search):
        pedido = self._criar_pedido_expirado(status_pagamento="pending")
        call_command("expirar_pedidos")
        pedido.refresh_from_db()
        self.produto.refresh_from_db()
        self.assertEqual(pedido.status, Pedido.Status.PAGO)
        self.assertEqual(pedido.status_pagamento, "approved")
        self.assertEqual(pedido.mercado_pago_payment_id, "mp-123")
        self.assertFalse(pedido.estoque_devolvido)
        self.assertEqual(self.produto.quantidade, 2)

    @patch("store.management.commands.expirar_pedidos.search_order_payments", return_value={"results": [{"id": "mp-pending", "status": "pending"}]})
    def test_rotina_nao_libera_estoque_com_pagamento_ainda_pendente(self, _search):
        pedido = self._criar_pedido_expirado(status_pagamento="pending")
        call_command("expirar_pedidos")
        pedido.refresh_from_db()
        self.produto.refresh_from_db()
        self.assertEqual(pedido.status, Pedido.Status.AGUARDANDO)
        self.assertFalse(pedido.estoque_devolvido)
        self.assertEqual(self.produto.quantidade, 2)

    def test_pagamento_pendente_expirado_nao_libera_estoque_sem_conciliacao(self):
        pedido = self._criar_pedido_expirado(status_pagamento="pending")
        response = self.client.post(
            f"/api/loja/pedidos/{pedido.id}/pagar/",
            {"metodo_pagamento": "pix"}, format="json",
        )
        self.assertEqual(response.status_code, 409)
        pedido.refresh_from_db()
        self.produto.refresh_from_db()
        self.assertEqual(pedido.status, Pedido.Status.AGUARDANDO)
        self.assertFalse(pedido.estoque_devolvido)
        self.assertEqual(self.produto.quantidade, 2)

    def test_pagamento_de_pedido_expirado_e_bloqueado_e_devolve_estoque(self):
        pedido = self._criar_pedido_expirado()
        response = self.client.post(
            f"/api/loja/pedidos/{pedido.id}/pagar/",
            {"metodo_pagamento": "pix"}, format="json",
        )
        self.assertEqual(response.status_code, 409)
        pedido.refresh_from_db()
        self.produto.refresh_from_db()
        self.assertEqual(pedido.status, Pedido.Status.CANCELADO)
        self.assertTrue(pedido.estoque_devolvido)
        self.assertEqual(self.produto.quantidade, 3)

    def test_produto_rejeita_preco_zero(self):
        serializer = ProdutoSerializer(self.produto, data={"preco": "0.00"}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("preco", serializer.errors)

    def test_produto_rejeita_imagem_acima_de_cinco_mb(self):
        upload = SimpleUploadedFile("grande.png", b"0" * (5 * 1024 * 1024 + 1), content_type="image/png")
        serializer = ProdutoSerializer(self.produto, data={"imagem": upload}, partial=True)
        self.assertFalse(serializer.is_valid())
        self.assertIn("imagem", serializer.errors)

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

    def test_admin_da_torcida_nao_pode_carregar_catalogo_demo(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post("/api/loja/catalogo-demo/", {"torcida": self.torcida.id}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_superusuario_pode_carregar_dez_produtos_demo(self):
        global_admin = get_user_model().objects.create_superuser(username="admin_global_catalogo", email="", password="Strong-Test-Password-2026!")
        self.client.force_authenticate(global_admin)
        response = self.client.post("/api/loja/catalogo-demo/", {"torcida": self.torcida.id}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Produto.objects.filter(torcida=self.torcida, ativo=True).count(), 11)
        self.assertEqual(response.data["total"], 10)

    def test_admin_da_torcida_nao_pode_criar_editar_ou_excluir_produtos(self):
        self.client.force_authenticate(self.admin)
        payload = {"torcida": self.torcida.id, "nome": "Restrito", "preco": "15.00", "quantidade": 2}
        self.assertEqual(self.client.post("/api/loja/produtos/", payload, format="json").status_code, 403)
        self.assertEqual(self.client.patch(f"/api/loja/produtos/{self.produto.id}/", {"nome": "Alterado"}, format="json").status_code, 403)
        self.assertEqual(self.client.delete(f"/api/loja/produtos/{self.produto.id}/").status_code, 403)



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
