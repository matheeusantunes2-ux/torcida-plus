from rest_framework import serializers
from .models import Torcida


class TorcidaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Torcida
        fields = ("id", "nome", "slug", "escudo_url", "cor_principal", "criada_em")
        read_only_fields = ("id", "criada_em")
