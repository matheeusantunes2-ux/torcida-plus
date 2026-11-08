from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from torcidas.models import Membro
from accounts.permissions import is_platform_admin
from .models import Publicacao, Notificacao
from .permissions import AutorPodeEditarPublicacao
from .serializers import PublicacaoSerializer


class PublicacaoViewSet(viewsets.ModelViewSet):
    serializer_class = PublicacaoSerializer
    permission_classes = [AutorPodeEditarPublicacao]

    def get_queryset(self):
        usuario = self.request.user

        queryset = Publicacao.objects.all()
        if not is_platform_admin(usuario):
            queryset = queryset.filter(
                torcida__membros__usuario=usuario,
                status=Publicacao.Status.APROVADA,
            )
        queryset = queryset.select_related("autor", "torcida").distinct()

        torcida_id = self.request.query_params.get("torcida")

        status_filtro = self.request.query_params.get("status")
        if status_filtro in Publicacao.Status.values:
            queryset = queryset.filter(status=status_filtro)

        if torcida_id:
            if not torcida_id.isdigit():
                raise ValidationError({
                    "torcida": "Informe um ID de torcida válido."
                })

            queryset = queryset.filter(torcida_id=int(torcida_id))

        return queryset

    def perform_create(self, serializer):
        serializer.save(autor=self.request.user, status=Publicacao.Status.PENDENTE)

    def _exigir_admin_global(self):
        if not is_platform_admin(self.request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Somente o administrador da plataforma pode aprovar publicações.")

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def aprovar(self, request, pk=None):
        self._exigir_admin_global()
        publicacao = self.get_object()
        publicacao.status = Publicacao.Status.APROVADA
        publicacao.save(update_fields=["status", "atualizada_em"])
        return Response(self.get_serializer(publicacao).data)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def rejeitar(self, request, pk=None):
        self._exigir_admin_global()
        publicacao = self.get_object()
        publicacao.status = Publicacao.Status.REJEITADA
        publicacao.save(update_fields=["status", "atualizada_em"])
        return Response(self.get_serializer(publicacao).data)


from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Comentario, Curtida
from .comentario_serializers import ComentarioSerializer
from .notificacao_serializers import NotificacaoSerializer


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
                torcida__membros__usuario=self.request.user,
                status=Publicacao.Status.APROVADA,
            ).distinct(),
            pk=self.kwargs["publicacao_id"],
        )

    def get_queryset(self):
        return Comentario.objects.filter(
            publicacao__torcida__membros__usuario=self.request.user,
            publicacao__status=Publicacao.Status.APROVADA,
            publicacao_id=self.kwargs["publicacao_id"],
        ).select_related("autor", "publicacao").distinct()

    def perform_create(self, serializer):
        publicacao = self.get_publicacao()
        serializer.save(publicacao=publicacao, autor=self.request.user)
        if publicacao.autor_id != self.request.user.id:
            Notificacao.objects.create(destinatario=publicacao.autor, ator=self.request.user, tipo=Notificacao.Tipo.COMENTARIO, texto="{} comentou na sua publicação.".format(self.request.user.username), referencia="publicacao:{}".format(publicacao.pk))


class CurtidaView(APIView):
    permission_classes = [IsAuthenticated]

    def obter_publicacao(self, request, publicacao_id):
        return get_object_or_404(
            Publicacao.objects.filter(
                torcida__membros__usuario=request.user,
                status=Publicacao.Status.APROVADA,
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
                curtida, criada = Curtida.objects.get_or_create(publicacao=publicacao, usuario=request.user)
                if criada and publicacao.autor_id != request.user.id:
                    Notificacao.objects.create(destinatario=publicacao.autor, ator=request.user, tipo=Notificacao.Tipo.CURTIDA, texto="{} curtiu sua publicação.".format(request.user.username), referencia="publicacao:{}".format(publicacao.pk))
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


class NotificacaoViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificacaoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notificacao.objects.filter(destinatario=self.request.user).select_related("ator")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        unread = queryset.filter(lida_em__isnull=True).count()
        page = self.paginate_queryset(queryset)
        data = self.get_serializer(page if page is not None else queryset, many=True).data
        if page is not None:
            response = self.get_paginated_response(data)
            response.data["nao_lidas"] = unread
            return response
        return Response({"nao_lidas": unread, "results": data})

    def mark_all_read(self, request):
        from django.utils import timezone
        self.get_queryset().filter(lida_em__isnull=True).update(lida_em=timezone.now())
        return Response({"mensagem": "Notificações marcadas como lidas."})

    def mark_one_read(self, request, pk=None):
        from django.utils import timezone
        item = get_object_or_404(self.get_queryset(), pk=pk)
        Notificacao.objects.filter(pk=item.pk, destinatario=request.user, lida_em__isnull=True).update(lida_em=timezone.now())
        return Response({"mensagem": "Notificação marcada como lida."})
