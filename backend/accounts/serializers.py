from io import BytesIO

from PIL import Image, UnidentifiedImageError
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Perfil

User = get_user_model()


class CadastroSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        password = validated_data.pop("password")
        usuario = User.objects.create_user(
            password=password,
            **validated_data,
        )
        Perfil.objects.get_or_create(usuario=usuario)
        return usuario


class PerfilSerializer(serializers.ModelSerializer):
    usuario_id = serializers.IntegerField(
        source="usuario.id",
        read_only=True,
    )
    username = serializers.CharField(
        source="usuario.username",
        read_only=True,
    )

    class Meta:
        model = Perfil
        fields = (
            "usuario_id",
            "username",
            "nome_exibicao",
            "biografia",
            "foto",
            "criado_em",
            "atualizado_em",
        )
        read_only_fields = (
            "usuario_id",
            "username",
            "criado_em",
            "atualizado_em",
        )

    def validate_nome_exibicao(self, valor):
        return valor.strip()

    def validate_biografia(self, valor):
        return valor.strip()

    def validate_foto(self, foto):
        if foto is None:
            return foto

        if foto.size > 5 * 1024 * 1024:
            raise serializers.ValidationError(
                "A foto deve ter no máximo 5 MB."
            )

        foto.seek(0)
        try:
            with Image.open(foto) as imagem:
                if imagem.format not in {"JPEG", "PNG", "WEBP"}:
                    raise serializers.ValidationError(
                        "Use uma imagem JPEG, PNG ou WEBP."
                    )

                largura, altura = imagem.size
                if largura * altura > 20_000_000:
                    raise serializers.ValidationError(
                        "A imagem possui dimensões excessivas."
                    )

                imagem.verify()

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
            foto.seek(0)

        return foto
