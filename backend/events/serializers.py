from rest_framework import serializers
from accounts.permissions import is_platform_admin
from torcidas.models import Membro
from .models import Evento


class EventoSerializer(serializers.ModelSerializer):
    torcida_nome = serializers.CharField(source="torcida.nome", read_only=True)
    criado_por_nome = serializers.CharField(source="criado_por.username", read_only=True)

    class Meta:
        model = Evento
        fields = [
            "id", "torcida", "torcida_nome", "titulo", "descricao", "tipo",
            "local", "inicio_em", "fim_em", "capacidade", "valor", "status",
            "criado_por", "criado_por_nome", "criado_em", "atualizado_em",
        ]
        read_only_fields = ["id", "criado_por", "criado_por_nome", "criado_em", "atualizado_em"]

    def validate(self, attrs):
        request = self.context["request"]
        torcida = attrs.get("torcida", getattr(self.instance, "torcida", None))
        if torcida is None:
            raise serializers.ValidationError({"torcida": "Informe a torcida."})
        if not is_platform_admin(request.user):
            membro = Membro.objects.filter(torcida=torcida, usuario=request.user).first()
            if membro is None or membro.papel not in (Membro.Papel.ADMIN, Membro.Papel.MODERADOR):
                raise serializers.ValidationError({"torcida": "Somente administradores e moderadores da torcida podem gerenciar eventos."})
        inicio = attrs.get("inicio_em", getattr(self.instance, "inicio_em", None))
        fim = attrs.get("fim_em", getattr(self.instance, "fim_em", None))
        if fim and inicio and fim <= inicio:
            raise serializers.ValidationError({"fim_em": "O término deve ser posterior ao início."})
        valor = attrs.get("valor", getattr(self.instance, "valor", 0))
        if valor < 0:
            raise serializers.ValidationError({"valor": "O valor não pode ser negativo."})
        return attrs

    def create(self, validated_data):
        return Evento.objects.create(criado_por=self.context["request"].user, **validated_data)
