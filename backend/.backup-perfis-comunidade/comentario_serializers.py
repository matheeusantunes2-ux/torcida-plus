from rest_framework import serializers

from .models import Comentario


class ComentarioSerializer(serializers.ModelSerializer):
    autor_id = serializers.IntegerField(
        source="autor.id",
        read_only=True,
    )
    autor_username = serializers.CharField(
        source="autor.username",
        read_only=True,
    )

    class Meta:
        model = Comentario
        fields = [
            "id",
            "autor_id",
            "autor_username",
            "texto",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "id",
            "autor_id",
            "autor_username",
            "criado_em",
            "atualizado_em",
        ]

    def validate_texto(self, texto):
        texto = texto.strip()

        if not texto:
            raise serializers.ValidationError(
                "O comentário não pode estar vazio."
            )

        return texto
