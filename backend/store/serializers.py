from rest_framework import serializers
from .models import Produto, ItemCarrinho, Pedido, ItemPedido

class ProdutoSerializer(serializers.ModelSerializer):
    imagem_url = serializers.SerializerMethodField()
    class Meta:
        model = Produto
        fields = ["id","torcida","nome","descricao","categoria","preco","quantidade","imagem","imagem_url","ativo","criado_em","atualizado_em"]
        read_only_fields = ["id","torcida","imagem_url","criado_em","atualizado_em"]
    def get_imagem_url(self,obj):
        request=self.context.get("request")
        if not obj.imagem: return None
        url=obj.imagem.url
        return request.build_absolute_uri(url) if request else url

class ItemCarrinhoSerializer(serializers.ModelSerializer):
    produto=ProdutoSerializer(read_only=True)
    produto_id=serializers.IntegerField(write_only=True)
    class Meta:
        model=ItemCarrinho
        fields=["id","produto","produto_id","quantidade"]

class ItemPedidoSerializer(serializers.ModelSerializer):
    class Meta:
        model=ItemPedido
        fields=["id","nome_produto","preco_unitario","quantidade","total"]

class PedidoSerializer(serializers.ModelSerializer):
    itens=ItemPedidoSerializer(many=True,read_only=True)
    class Meta:
        model=Pedido
        fields=["id","torcida","comprador","status","nome_destinatario","telefone","cep","endereco","numero","complemento","bairro","cidade","uf","observacoes","total","metodo_pagamento","status_pagamento","criado_em","itens"]
        read_only_fields=fields
