from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from community.models import Notificacao

from .models import Conversa, ParticipanteConversa, Mensagem
from .serializers import ConversaSerializer, MensagemSerializer


def conversas_do_usuario(usuario):
    return Conversa.objects.filter(
        participantes__usuario=usuario, participantes__ativo=True
    ).select_related("torcida").distinct()


def obter_conversa(usuario, conversa_id):
    return get_object_or_404(conversas_do_usuario(usuario), pk=conversa_id)


class ListaCriarConversaView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = conversas_do_usuario(request.user).prefetch_related("participantes")
        return Response(ConversaSerializer(queryset, many=True, context={"request": request}).data)

    def post(self, request):
        serializer = ConversaSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        conversa = serializer.save()
        return Response(
            ConversaSerializer(conversa, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ListaCriarMensagemView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, conversa_id):
        conversa = obter_conversa(request.user, conversa_id)
        queryset = conversa.mensagens.filter(apagada_em__isnull=True).select_related("autor")
        before_id = request.query_params.get("before_id")
        if before_id:
            if not before_id.isdigit():
                raise ValidationError({"before_id": "Informe um ID válido."})
            queryset = queryset.filter(id__lt=int(before_id))
        mensagens = queryset.order_by("-id")[:50]
        data = list(reversed(list(mensagens)))
        return Response(MensagemSerializer(data, many=True).data)

    def post(self, request, conversa_id):
        conversa = obter_conversa(request.user, conversa_id)
        serializer = MensagemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            mensagem = Mensagem.objects.create(
                conversa=conversa, autor=request.user,
                conteudo=serializer.validated_data["conteudo"],
            )
            conversa.save(update_fields=["atualizada_em"])
            destinatarios = conversa.participantes.filter(
                ativo=True
            ).exclude(usuario=request.user).values_list("usuario_id", flat=True)
            Notificacao.objects.bulk_create([
                Notificacao(
                    destinatario_id=usuario_id,
                    ator=request.user,
                    tipo=Notificacao.Tipo.MENSAGEM,
                    texto="Você recebeu uma nova mensagem.",
                    referencia=f"conversa:{conversa.pk}",
                )
                for usuario_id in destinatarios
            ])
        return Response(MensagemSerializer(mensagem).data, status=status.HTTP_201_CREATED)
