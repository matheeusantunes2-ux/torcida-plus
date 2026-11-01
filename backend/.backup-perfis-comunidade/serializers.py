from PIL import Image, UnidentifiedImageError
from rest_framework import serializers

from torcidas.models import Membro, Torcida
from .models import Publicacao


class PublicacaoSerializer(serializers.ModelSerializer):
    autor_id = serializers.IntegerField(
        source="autor.id",
        read_only=True,
    )
    autor_username = serializers.CharField(
        source="autor.username",
        read_only=True,
    )

    torcida = serializers.PrimaryKeyRelatedField(
        queryset=Torcida.objects.all()
    )

    class Meta:
        model = Publicacao
        fields = [
            "id",
            "torcida",
            "autor_id",
            "autor_username",
            "texto",
            "imagem",
            "criada_em",
            "atualizada_em",
        ]
        read_only_fields = [
            "id",
            "autor_id",
            "autor_username",
            "criada_em",
            "atualizada_em",
        ]

    def validate_torcida(self, torcida):
        usuario = self.context["request"].user

        participa = Membro.objects.filter(
            torcida=torcida,
            usuario=usuario,
        ).exists()

        if not participa:
            raise serializers.ValidationError(
                "Você precisa participar desta torcida para publicar."
            )

        return torcida

    def validate_imagem(self, imagem):
        if imagem is None:
            return imagem

        limite_bytes = 5 * 1024 * 1024
        formatos_permitidos = {"JPEG", "PNG", "WEBP"}
        imagem.seek(0)

        try:
            if imagem.size > limite_bytes:
                raise serializers.ValidationError(
                    "A imagem deve ter no máximo 5 MB."
                )

            with Image.open(imagem) as img:
                formato = img.format
                largura, altura = img.size

                if formato not in formatos_permitidos:
                    raise serializers.ValidationError(
                        "Formato inválido. Use JPEG, PNG ou WEBP."
                    )

                if largura * altura > 20_000_000:
                    raise serializers.ValidationError(
                        "A imagem possui dimensões excessivas."
                    )

                img.verify()

        except serializers.ValidationError:
            raise
        except (
            UnidentifiedImageError,
            OSError,
            Image.DecompressionBombError,
        ):
            raise serializers.ValidationError(
                "O arquivo enviado não é uma imagem válida."
            )
        finally:
            imagem.seek(0)

        return imagem

    def validate_texto(self, texto):
        if not texto.strip():
            raise serializers.ValidationError(
                "A publicação não pode estar vazia."
            )

        return texto.strip()
