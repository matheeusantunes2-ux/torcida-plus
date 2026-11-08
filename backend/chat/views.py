import os
import uuid
from datetime import datetime, timedelta, timezone as datetime_timezone

import cloudinary
from cloudinary import uploader
from cloudinary.utils import private_download_url
from PIL import Image, UnidentifiedImageError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from community.models import Notificacao
from accounts.permissions import is_platform_admin
from .models import AnexoMensagem, Conversa
from .serializers import ConversaSerializer, MensagemSerializer


MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_VIDEO_BYTES = 100 * 1024 * 1024
IMAGE_TYPES = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/gif": "gif",
}
VIDEO_TYPES = {
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/quicktime": "mov",
}
AUDIO_TYPES = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mpeg": "mp3", "audio/mp4": "m4a", "audio/wav": "wav", "audio/x-wav": "wav"}
MAX_AUDIO_BYTES = 25 * 1024 * 1024


def conversas_do_usuario(usuario):
    queryset = Conversa.objects.select_related("torcida")
    if is_platform_admin(usuario):
        return queryset.all()
    return queryset.filter(participantes__usuario=usuario, participantes__ativo=True, torcida__membros__usuario=usuario).distinct()


def obter_conversa(usuario, conversa_id):
    return get_object_or_404(conversas_do_usuario(usuario), pk=conversa_id)


def validar_arquivo(upload):
    content_type = (upload.content_type or "").lower()
    if content_type in IMAGE_TYPES:
        if upload.size > MAX_IMAGE_BYTES:
            raise ValidationError({"arquivo": "Imagens devem ter no máximo 12 MB."})
        try:
            image = Image.open(upload)
            image.verify()
            detected = Image.MIME.get(image.format)
        except (UnidentifiedImageError, OSError, ValueError):
            raise ValidationError({"arquivo": "O arquivo não é uma imagem válida."})
        finally:
            upload.seek(0)
        if detected != content_type:
            raise ValidationError({"arquivo": "O tipo real da imagem não corresponde ao arquivo enviado."})
        return "image", IMAGE_TYPES[content_type], "imagem", content_type
    if content_type in VIDEO_TYPES:
        if upload.size > MAX_VIDEO_BYTES:
            raise ValidationError({"arquivo": "Vídeos devem ter no máximo 100 MB."})
        header = upload.read(32)
        upload.seek(0)
        if content_type == "video/mp4" and (len(header) < 12 or header[4:8] != b"ftyp"):
            raise ValidationError({"arquivo": "O arquivo MP4 não passou na validação."})
        if content_type == "video/webm" and not header.startswith(b"\x1aE\xdf\xa3"):
            raise ValidationError({"arquivo": "O arquivo WebM não passou na validação."})
        if content_type == "video/quicktime" and (len(header) < 12 or header[4:8] != b"ftyp"):
            raise ValidationError({"arquivo": "O arquivo MOV não passou na validação."})
        return "video", VIDEO_TYPES[content_type], "video", content_type
    if content_type in AUDIO_TYPES:
        if upload.size > MAX_AUDIO_BYTES:
            raise ValidationError({"arquivo": "Áudios devem ter no máximo 25 MB."})
        header = upload.read(16)
        upload.seek(0)
        valid = (
            (content_type == "audio/webm" and header.startswith(bytes([0x1a, 0x45, 0xdf, 0xa3]))) or
            (content_type == "audio/ogg" and header.startswith(b"OggS")) or
            (content_type == "audio/mpeg" and (header.startswith(b"ID3") or (len(header) > 1 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0))) or
            (content_type == "audio/mp4" and len(header) >= 8 and header[4:8] == b"ftyp") or
            (content_type in ("audio/wav", "audio/x-wav") and header.startswith(b"RIFF") and header[8:12] == b"WAVE")
        )
        if not valid:
            raise ValidationError({"arquivo": "O áudio não passou na validação do formato."})
        return "video", AUDIO_TYPES[content_type], "audio", content_type
    raise ValidationError({"arquivo": "Formato não permitido. Envie imagens, vídeos ou áudios nos formatos aceitos."})


class ListaCriarConversaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = conversas_do_usuario(request.user).prefetch_related("participantes")
        return Response(ConversaSerializer(queryset, many=True, context={"request": request}).data)

    def post(self, request):
        serializer = ConversaSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        conversa = serializer.save()
        return Response(ConversaSerializer(conversa, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ListaCriarMensagemView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversa_id):
        conversa = obter_conversa(request.user, conversa_id)
        queryset = conversa.mensagens.filter(apagada_em__isnull=True).select_related("autor").prefetch_related("anexos")
        before_id = request.query_params.get("before_id")
        if before_id:
            if not before_id.isdigit():
                raise ValidationError({"before_id": "Informe um ID válido."})
            queryset = queryset.filter(id__lt=int(before_id))
        mensagens = queryset.order_by("-id")[:50]
        return Response(MensagemSerializer(list(reversed(list(mensagens))), many=True, context={"request": request}).data)

    def post(self, request, conversa_id):
        conversa = obter_conversa(request.user, conversa_id)
        serializer = MensagemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            mensagem = conversa.mensagens.create(autor=request.user, conteudo=serializer.validated_data["conteudo"])
            conversa.save(update_fields=["atualizada_em"])
            destinatarios = conversa.participantes.filter(ativo=True).exclude(usuario=request.user).values_list("usuario_id", flat=True)
            Notificacao.objects.bulk_create([
                Notificacao(destinatario_id=user_id, ator=request.user, tipo=Notificacao.Tipo.MENSAGEM,
                            texto="Você recebeu uma nova mensagem.", referencia=f"conversa:{conversa.pk}")
                for user_id in destinatarios
            ])
        return Response(MensagemSerializer(mensagem, context={"request": request}).data, status=status.HTTP_201_CREATED)


class EnviarAnexoMensagemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversa_id):
        conversa = obter_conversa(request.user, conversa_id)
        upload = request.FILES.get("arquivo")
        if not upload:
            raise ValidationError({"arquivo": "Selecione uma imagem ou vídeo."})
        resource_type, extension, kind, content_type = validar_arquivo(upload)
        if not os.getenv("CLOUDINARY_URL"):
            return Response({"detail": "Armazenamento ainda não configurado. Configure CLOUDINARY_URL no Render."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        cloudinary.config(secure=True)
        public_id = f"torcida-plus/chat/{conversa.pk}/{uuid.uuid4().hex}"
        try:
            result = uploader.upload(upload, resource_type=resource_type, type="authenticated",
                                     public_id=public_id, overwrite=False, use_filename=False,
                                     unique_filename=False, timeout=90)
        except Exception:
            return Response({"detail": "Não foi possível armazenar o arquivo. Verifique a configuração do Cloudinary e tente novamente."}, status=status.HTTP_502_BAD_GATEWAY)
        caption = (request.data.get("conteudo") or "").strip()[:4000]
        if not caption:
            caption = "📷 Imagem" if kind == "imagem" else ("🎙️ Áudio" if kind == "audio" else "🎥 Vídeo")
        try:
            with transaction.atomic():
                mensagem = conversa.mensagens.create(autor=request.user, conteudo=caption)
                AnexoMensagem.objects.create(mensagem=mensagem, tipo=kind,
                    cloudinary_public_id=result["public_id"], cloudinary_resource_type=resource_type,
                    formato=result.get("format", extension), nome_original=os.path.basename(upload.name)[:255],
                    content_type=content_type, tamanho=upload.size)
                Conversa.objects.filter(pk=conversa.pk).update(atualizada_em=timezone.now())
                destinatarios = conversa.participantes.filter(ativo=True).exclude(usuario=request.user).values_list("usuario_id", flat=True)
                Notificacao.objects.bulk_create([
                    Notificacao(destinatario_id=user_id, ator=request.user, tipo=Notificacao.Tipo.MENSAGEM,
                                texto="Você recebeu uma mídia no chat.", referencia=f"conversa:{conversa.pk}")
                    for user_id in destinatarios
                ])
        except Exception:
            try:
                uploader.destroy(result["public_id"], resource_type=resource_type, type="authenticated")
            except Exception:
                pass
            raise
        mensagem = conversa.mensagens.prefetch_related("anexos").get(pk=mensagem.pk)
        return Response(MensagemSerializer(mensagem, context={"request": request}).data, status=status.HTTP_201_CREATED)


class ObterUrlAnexoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, anexo_id):
        anexo = get_object_or_404(AnexoMensagem.objects.select_related("mensagem__conversa"), pk=anexo_id)
        obter_conversa(request.user, anexo.mensagem.conversa_id)
        expires_at = int((datetime.now(datetime_timezone.utc) + timedelta(seconds=90)).timestamp())
        try:
            url = private_download_url(anexo.cloudinary_public_id, anexo.formato,
                resource_type=anexo.cloudinary_resource_type, type="authenticated", expires_at=expires_at)
        except Exception:
            return Response({"detail": "Não foi possível gerar o acesso temporário à mídia."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({"url": url, "expires_in": 90})
