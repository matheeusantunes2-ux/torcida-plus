from rest_framework import serializers
from PIL import Image, UnidentifiedImageError
from .models import Produto, ItemCarrinho, Pedido, ItemPedido

MAX_PRODUCT_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_PRODUCT_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}

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

    def validate_preco(self, value):
        if value <= 0:
            raise serializers.ValidationError("O preço deve ser maior que zero.")
        return value

    def validate_quantidade(self, value):
        if value < 0:
            raise serializers.ValidationError("O estoque não pode ser negativo.")
        return value

    def validate_imagem(self, value):
        if value.size > MAX_PRODUCT_IMAGE_BYTES:
            raise serializers.ValidationError("A imagem deve ter no máximo 5 MB.")
        try:
            image = Image.open(value)
            if image.format not in ALLOWED_PRODUCT_IMAGE_FORMATS:
                raise serializers.ValidationError("Use uma imagem JPEG, PNG ou WEBP.")
            image.verify()
        except (UnidentifiedImageError, OSError, ValueError):
            raise serializers.ValidationError("O arquivo enviado não é uma imagem válida.")
        finally:
            value.seek(0)
        return value

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
