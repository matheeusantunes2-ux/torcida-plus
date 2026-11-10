from rest_framework import serializers
from .models import Membro


class MembroSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="usuario.username",
        read_only=True,
    )

    pelotao_nome = serializers.CharField(source="pelotao.nome", read_only=True, allow_null=True)

    class Meta:
        model = Membro
        fields = ["id", "usuario", "username", "papel", "pelotao", "pelotao_nome", "criado_em"]
        read_only_fields = ["id", "username", "pelotao_nome", "criado_em"]
