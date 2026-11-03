from rest_framework import serializers

from torcidas.models import Membro
from .models import Produto


class ProdutoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Produto
        fields = [
            "id",
            "torcida",
            "nome",
            "descricao",
            "preco",
            "imagem",
            "disponivel",
            "criado_em",
        ]
        read_only_fields = ["id", "criado_em"]

    def validate_torcida(self, torcida):
        usuario = self.context["request"].user
        if not Membro.objects.filter(torcida=torcida, usuario=usuario).exists():
            raise serializers.ValidationError("Você precisa participar da torcida para listar produtos.")
        return torcida

