from PIL import Image, UnidentifiedImageError
from django.core import signing
from django.urls import reverse
from urllib.parse import urlencode
from pathlib import PurePosixPath
from rest_framework import serializers

from torcidas.models import Membro, Torcida
from .models import Publicacao


class SignedPublicationImageField(serializers.ImageField):
    """Gera URL temporária vinculada a membro autorizado da torcida."""

    def get_attribute(self, instance):
        self._current_publicacao = instance
        return super().get_attribute(instance)

    def to_representation(self, value):
        if not value:
            return None
        request = self.context.get("request")
        publicacao = getattr(self, "_current_publicacao", None)
        if not request or not request.user.is_authenticated or not publicacao:
            return None
        token = signing.dumps(
            {
                "publicacao_id": publicacao.pk,
                "usuario_id": request.user.pk,
                "arquivo": value.name,
            },
            salt="torcida-publicacao-media-v1",
        )
        caminho_relativo = value.name.removeprefix("publicacoes/")
        path = reverse("media-publicacao", kwargs={"path": caminho_relativo})
        url = f"{path}?{urlencode({'token': token})}"
        return request.build_absolute_uri(url)


class SignedPublicationFileField(serializers.FileField):
    """URL assinada de anexo, limitada ao usuário autenticado."""
    def __init__(self, media_kind, *args, **kwargs):
        self.media_kind = media_kind
        super().__init__(*args, **kwargs)

    def get_attribute(self, instance):
        self._current_publicacao = instance
        return super().get_attribute(instance)

    def to_representation(self, value):
        if not value:
            return None
        request = self.context.get("request")
        post = getattr(self, "_current_publicacao", None)
        if not request or not request.user.is_authenticated or not post:
            return None
        token = signing.dumps({"publicacao_id": post.pk, "usuario_id": request.user.pk, "arquivo": value.name, "tipo": self.media_kind}, salt="torcida-publicacao-media-v1")
        relative = value.name.removeprefix(f"publicacoes/{self.media_kind}/")
        path = reverse("media-publicacao-anexo", kwargs={"kind": self.media_kind, "path": relative})
        return request.build_absolute_uri(f"{path}?{urlencode({'token': token})}")


class PublicacaoSerializer(serializers.ModelSerializer):
    texto = serializers.CharField(max_length=5000, required=False, allow_blank=True)
    imagem = SignedPublicationImageField(required=False, allow_null=True)
    audio = SignedPublicationFileField("audio", required=False, allow_null=True)
    arquivo = SignedPublicationFileField("arquivos", required=False, allow_null=True)

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

    autor_nome_exibicao = serializers.SerializerMethodField()
    autor_foto = serializers.SerializerMethodField()
    total_curtidas = serializers.SerializerMethodField()
    total_comentarios = serializers.SerializerMethodField()
    curtida_pelo_usuario = serializers.SerializerMethodField()

    class Meta:
        model = Publicacao
        fields = [
            "id",
            "torcida",
            "autor_id",
            "autor_username",
            "autor_nome_exibicao",
            "autor_foto",
            "total_curtidas",
            "total_comentarios",
            "curtida_pelo_usuario",
            "texto",
            "status",
            "imagem",
            "audio",
            "arquivo",
            "criada_em",
            "atualizada_em",
        ]
        read_only_fields = [
            "id",
            "autor_id",
            "autor_username",
            "autor_nome_exibicao",
            "autor_foto",
            "criada_em",
            "atualizada_em",
            "status",
        ]

    def get_autor_nome_exibicao(self, obj):
        perfil = getattr(obj.autor, "perfil", None)
        nome = perfil.nome_exibicao.strip() if perfil else ""
        return nome or obj.autor.username

    def get_total_curtidas(self, obj):
        return obj.curtidas.count()

    def get_total_comentarios(self, obj):
        return obj.comentarios.count()

    def get_curtida_pelo_usuario(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.curtidas.filter(usuario=request.user).exists())

    def get_autor_foto(self, obj):
        perfil = getattr(obj.autor, "perfil", None)
        if not perfil or not perfil.foto:
            return None
        request = self.context.get("request")
        url = perfil.foto.url
        return request.build_absolute_uri(url) if request else url

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


    def _validate_upload(self, upload, extensions, limit, label):
        if upload is None:
            return upload
        if PurePosixPath(upload.name).suffix.lower() not in extensions:
            raise serializers.ValidationError(f"Formato de {label} não permitido.")
        if upload.size > limit:
            raise serializers.ValidationError(f"{label.capitalize()} excede o limite de {limit // (1024 * 1024)} MB.")
        return upload

    def validate_audio(self, upload):
        return self._validate_upload(upload, {".mp3", ".m4a", ".aac", ".ogg", ".wav", ".webm"}, 15 * 1024 * 1024, "áudio")

    def validate_arquivo(self, upload):
        return self._validate_upload(upload, {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".odt", ".ods", ".odp"}, 20 * 1024 * 1024, "documento")

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not attrs.get("texto") and not any(attrs.get(k) for k in ("imagem", "audio", "arquivo")):
            raise serializers.ValidationError({"texto": "Escreva algo ou anexe uma mídia."})
        return attrs

    def validate_texto(self, texto):
        return texto.strip()
