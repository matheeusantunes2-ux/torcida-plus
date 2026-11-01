from rest_framework import serializers
from .models import Membro


class MembroSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="usuario.username",
        read_only=True,
    )

    class Meta:
        model = Membro
        fields = ["id", "usuario", "username", "papel", "criado_em"]
        read_only_fields = ["id", "username", "criado_em"]
