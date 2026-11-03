from rest_framework import serializers

from torcidas.models import Membro
from .models import Evento


class EventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evento
        fields = [
            "id",
            "torcida",
            "titulo",
            "descricao",
            "local",
            "data_inicio",
            "data_fim",
            "criado_por",
            "criado_em",
        ]
        read_only_fields = ["id", "criado_por", "criado_em"]

    def validate_torcida(self, torcida):
        usuario = self.context["request"].user
        if not Membro.objects.filter(torcida=torcida, usuario=usuario).exists():
            raise serializers.ValidationError("Você precisa ser membro da torcida para criar eventos.")
        return torcida

