from django.conf import settings
from django.db import models
from torcidas.models import Torcida


class Produto(models.Model):
    torcida = models.ForeignKey(Torcida, on_delete=models.CASCADE, related_name="produtos")
    nome = models.CharField(max_length=140)
    descricao = models.TextField(blank=True)
    categoria = models.CharField(max_length=60, default="Geral")
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.PositiveIntegerField(default=0)
    imagem = models.ImageField(upload_to="loja/produtos/", blank=True, null=True)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nome"]
        indexes = [models.Index(fields=["torcida", "ativo"], name="store_prod_torcida_idx")]

    def __str__(self):
        return self.nome


class Pedido(models.Model):
    class Status(models.TextChoices):
        AGUARDANDO = "aguardando", "Aguardando pagamento"
        PAGO = "pago", "Pago"
        SEPARACAO = "separacao", "Em separação"
        ENVIADO = "enviado", "Enviado"
        CONCLUIDO = "concluido", "Concluído"
        CANCELADO = "cancelado", "Cancelado"

    torcida = models.ForeignKey(Torcida, on_delete=models.PROTECT, related_name="pedidos_loja")
    comprador = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pedidos_loja")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.AGUARDANDO)
    nome_destinatario = models.CharField(max_length=140)
    telefone = models.CharField(max_length=30)
    cep = models.CharField(max_length=9)
    endereco = models.CharField(max_length=180)
    numero = models.CharField(max_length=20)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    uf = models.CharField(max_length=2)
    observacoes = models.CharField(max_length=500, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_pagamento = models.CharField(max_length=20, blank=True, default="")
    status_pagamento = models.CharField(max_length=20, default="nao_iniciado")
    mercado_pago_preference_id = models.CharField(max_length=100, blank=True, default="")
    mercado_pago_payment_id = models.CharField(max_length=100, blank=True, default="")
    checkout_url = models.URLField(max_length=500, blank=True, default="")
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]


class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="itens")
    produto = models.ForeignKey(Produto, on_delete=models.PROTECT, related_name="itens_vendidos")
    nome_produto = models.CharField(max_length=140)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)


class ItemCarrinho(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="itens_carrinho")
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE, related_name="itens_carrinho")
    quantidade = models.PositiveIntegerField(default=1)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["usuario", "produto"], name="carrinho_produto_unico")]
