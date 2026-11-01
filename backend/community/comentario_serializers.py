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

    autor_nome_exibicao = serializers.SerializerMethodField()
    autor_foto = serializers.SerializerMethodField()

    class Meta:
        model = Comentario
        fields = [
            "id",
            "autor_id",
            "autor_username",
            "autor_nome_exibicao",
            "autor_foto",
            "texto",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "id",
            "autor_id",
            "autor_username",
            "autor_nome_exibicao",
            "autor_foto",
            "criado_em",
            "atualizado_em",
        ]

    def get_autor_nome_exibicao(self, obj):
        perfil = getattr(obj.autor, "perfil", None)
        nome = perfil.nome_exibicao.strip() if perfil else ""
        return nome or obj.autor.username

    def get_autor_foto(self, obj):
        perfil = getattr(obj.autor, "perfil", None)
        if not perfil or not perfil.foto:
            return None
        request = self.context.get("request")
        url = perfil.foto.url
        return request.build_absolute_uri(url) if request else url

    def validate_texto(self, texto):
        texto = texto.strip()

        if not texto:
            raise serializers.ValidationError(
                "O comentário não pode estar vazio."
            )

        return texto
