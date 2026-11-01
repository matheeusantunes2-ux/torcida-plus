from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from torcidas.models import Membro
from .models import Publicacao
from .permissions import AutorPodeEditarPublicacao
from .serializers import PublicacaoSerializer


class PublicacaoViewSet(viewsets.ModelViewSet):
    serializer_class = PublicacaoSerializer
    permission_classes = [AutorPodeEditarPublicacao]

    def get_queryset(self):
        usuario = self.request.user

        queryset = Publicacao.objects.filter(
            torcida__membros__usuario=usuario
        ).select_related("autor", "torcida").distinct()

        torcida_id = self.request.query_params.get("torcida")

        if torcida_id:
            if not torcida_id.isdigit():
                raise ValidationError({
                    "torcida": "Informe um ID de torcida válido."
                })

            queryset = queryset.filter(torcida_id=int(torcida_id))

        return queryset

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user)


from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comentario, Curtida
from .comentario_serializers import ComentarioSerializer


class ComentarioViewSet(viewsets.ModelViewSet):
    serializer_class = ComentarioSerializer
    permission_classes = [AutorPodeEditarPublicacao]
    http_method_names = [
        "get", "post", "patch", "delete", "head", "options"
    ]
    lookup_url_kwarg = "comentario_id"

    def get_publicacao(self):
        return get_object_or_404(
            Publicacao.objects.filter(
                torcida__membros__usuario=self.request.user
            ).distinct(),
            pk=self.kwargs["publicacao_id"],
        )

    def get_queryset(self):
        return Comentario.objects.filter(
            publicacao__torcida__membros__usuario=self.request.user,
            publicacao_id=self.kwargs["publicacao_id"],
        ).select_related("autor", "publicacao").distinct()

    def perform_create(self, serializer):
        publicacao = self.get_publicacao()
        serializer.save(
            publicacao=publicacao,
            autor=self.request.user,
        )


class CurtidaView(APIView):
    permission_classes = [IsAuthenticated]

    def obter_publicacao(self, request, publicacao_id):
        return get_object_or_404(
            Publicacao.objects.filter(
                torcida__membros__usuario=request.user
            ).distinct(),
            pk=publicacao_id,
        )

    def get(self, request, publicacao_id):
        publicacao = self.obter_publicacao(request, publicacao_id)

        return Response({
            "publicacao_id": publicacao.pk,
            "total_curtidas": publicacao.curtidas.count(),
            "curtida_pelo_usuario": publicacao.curtidas.filter(
                usuario=request.user
            ).exists(),
        })

    def post(self, request, publicacao_id):
        publicacao = self.obter_publicacao(request, publicacao_id)

        try:
            with transaction.atomic():
                curtida, criada = Curtida.objects.get_or_create(
                    publicacao=publicacao,
                    usuario=request.user,
                )
        except IntegrityError:
            # Proteção adicional para requisições simultâneas.
            criada = False

        return Response(
            {
                "publicacao_id": publicacao.pk,
                "curtida_pelo_usuario": True,
                "total_curtidas": publicacao.curtidas.count(),
                "mensagem": (
                    "Curtida registrada."
                    if criada else "Você já curtiu esta publicação."
                ),
            },
            status=(
                status.HTTP_201_CREATED
                if criada else status.HTTP_200_OK
            ),
        )

    def delete(self, request, publicacao_id):
        publicacao = self.obter_publicacao(request, publicacao_id)

        Curtida.objects.filter(
            publicacao=publicacao,
            usuario=request.user,
        ).delete()

        return Response({
            "publicacao_id": publicacao.pk,
            "curtida_pelo_usuario": False,
            "total_curtidas": publicacao.curtidas.count(),
        })
