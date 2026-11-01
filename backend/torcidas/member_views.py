from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Torcida, Membro
from .member_serializers import MembroSerializer


User = get_user_model()


def obter_torcida(request, torcida_id):
    # Retorna apenas torcidas das quais o usuário participa.
    return get_object_or_404(
        Torcida.objects.filter(membros__usuario=request.user).distinct(),
        pk=torcida_id,
    )


def exigir_admin(request, torcida):
    membro = Membro.objects.filter(
        torcida=torcida,
        usuario=request.user,
    ).first()

    if membro is None or membro.papel != "admin":
        raise PermissionDenied(
            "Somente o administrador desta torcida pode gerenciar membros."
        )


class ListaMembrosView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, torcida_id):
        torcida = obter_torcida(request, torcida_id)

        membros = Membro.objects.filter(
            torcida=torcida
        ).select_related("usuario").order_by("id")

        return Response(MembroSerializer(membros, many=True).data)

    def post(self, request, torcida_id):
        torcida = obter_torcida(request, torcida_id)
        exigir_admin(request, torcida)

        usuario_id = request.data.get("usuario_id")
        papel = request.data.get("papel", "membro")

        if not usuario_id:
            raise ValidationError({
                "usuario_id": "Informe o ID do usuário que será adicionado."
            })

        # Não é permitido criar administradores por este endpoint.
        if papel not in ("membro", "moderador"):
            raise ValidationError({
                "papel": "Use 'membro' ou 'moderador'."
            })

        usuario = get_object_or_404(User, pk=usuario_id)

        if usuario.pk == request.user.pk:
            raise ValidationError(
                "Você já participa desta torcida."
            )

        if Membro.objects.filter(
            torcida=torcida,
            usuario=usuario,
        ).exists():
            raise ValidationError(
                "Este usuário já participa desta torcida."
            )

        try:
            with transaction.atomic():
                membro = Membro.objects.create(
                    torcida=torcida,
                    usuario=usuario,
                    papel=papel,
                )
        except IntegrityError:
            raise ValidationError(
                "Não foi possível adicionar o membro. Verifique se ele já participa."
            )

        return Response(
            MembroSerializer(membro).data,
            status=status.HTTP_201_CREATED,
        )


class DetalheMembroView(APIView):
    permission_classes = [IsAuthenticated]

    def obter_membro(self, request, torcida, membro_id):
        return get_object_or_404(
            Membro.objects.select_related("usuario").filter(
                torcida=torcida,
            ),
            pk=membro_id,
        )

    def patch(self, request, torcida_id, membro_id):
        torcida = obter_torcida(request, torcida_id)
        exigir_admin(request, torcida)

        membro = self.obter_membro(request, torcida, membro_id)

        # Não permite alterar o papel de um administrador.
        if membro.papel == "admin":
            raise ValidationError(
                "A transferência de administração exige um procedimento específico."
            )

        papel = request.data.get("papel")

        if papel not in ("membro", "moderador"):
            raise ValidationError({
                "papel": "O papel deve ser 'membro' ou 'moderador'."
            })

        membro.papel = papel
        membro.save(update_fields=["papel"])

        return Response(MembroSerializer(membro).data)

    def delete(self, request, torcida_id, membro_id):
        torcida = obter_torcida(request, torcida_id)
        exigir_admin(request, torcida)

        membro = self.obter_membro(request, torcida, membro_id)

        # A conta do usuário permanece intacta.
        if membro.papel == "admin":
            raise ValidationError(
                "Não é permitido remover um administrador por este endpoint."
            )

        membro.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
