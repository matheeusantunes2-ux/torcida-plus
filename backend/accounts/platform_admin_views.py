from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import is_platform_admin
from community.models import Publicacao
from torcidas.models import Membro, Torcida

User = get_user_model()


class PlatformAdminAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def check_admin(self, request):
        if not is_platform_admin(request.user):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("Acesso exclusivo ao administrador global do TORCIDA+.")


class PlatformAdminOverviewView(PlatformAdminAPIView):
    def get(self, request):
        self.check_admin(request)
        return Response({
            "usuarios_total": User.objects.count(),
            "usuarios_ativos": User.objects.filter(is_active=True).count(),
            "usuarios_bloqueados": User.objects.filter(is_active=False).count(),
            "torcidas_total": Torcida.objects.count(),
            "integrantes_total": Membro.objects.count(),
            "publicacoes_pendentes": Publicacao.objects.filter(status=Publicacao.Status.PENDENTE).count(),
            "publicacoes_aprovadas": Publicacao.objects.filter(status=Publicacao.Status.APROVADA).count(),
            "publicacoes_rejeitadas": Publicacao.objects.filter(status=Publicacao.Status.REJEITADA).count(),
        })


class PlatformAdminUsersView(PlatformAdminAPIView):
    def get(self, request):
        self.check_admin(request)
        queryset = User.objects.annotate(
            total_torcidas=Count("vinculos_torcidas", distinct=True)
        ).order_by("-date_joined")
        search = request.query_params.get("q", "").strip()
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) | Q(email__icontains=search)
            )
        status_filter = request.query_params.get("status")
        if status_filter == "ativos":
            queryset = queryset.filter(is_active=True)
        elif status_filter == "bloqueados":
            queryset = queryset.filter(is_active=False)
        try:
            page = max(1, int(request.query_params.get("page", "1")))
        except (TypeError, ValueError):
            page = 1
        page_size = 30
        total = queryset.count()
        users = queryset[(page - 1) * page_size:page * page_size]
        return Response({
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": [{
                "id": user.pk,
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
                "date_joined": user.date_joined,
                "last_login": user.last_login,
                "total_torcidas": user.total_torcidas,
            } for user in users],
        })


class PlatformAdminTorcidasView(PlatformAdminAPIView):
    def get(self, request):
        self.check_admin(request)
        queryset = Torcida.objects.annotate(
            total_membros=Count("membros", distinct=True),
            total_publicacoes=Count("publicacoes", distinct=True),
        ).order_by("-criada_em")
        return Response({
            "count": queryset.count(),
            "results": [{
                "id": torcida.pk,
                "nome": torcida.nome,
                "slug": torcida.slug,
                "criada_em": torcida.criada_em,
                "total_membros": torcida.total_membros,
                "total_publicacoes": torcida.total_publicacoes,
            } for torcida in queryset[:100]],
        })


class PlatformAdminUserStatusView(PlatformAdminAPIView):
    """Permite ao administrador global bloquear ou reativar contas comuns."""

    def patch(self, request, user_id):
        self.check_admin(request)
        if not isinstance(request.data.get("is_active"), bool):
            return Response(
                {"detail": "Informe is_active como true ou false."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        target = User.objects.filter(pk=user_id).first()
        if target is None:
            return Response({"detail": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND)
        if target.pk == request.user.pk:
            return Response(
                {"detail": "Você não pode alterar o status da própria conta por este painel."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if target.is_superuser:
            return Response(
                {"detail": "Contas de administrador global não podem ser bloqueadas por este recurso."},
                status=status.HTTP_403_FORBIDDEN,
            )
        target.is_active = request.data["is_active"]
        target.save(update_fields=["is_active"])
        return Response({
            "id": target.pk,
            "username": target.username,
            "is_active": target.is_active,
            "detail": "Conta reativada com sucesso." if target.is_active else "Conta bloqueada com sucesso.",
        })


class PlatformAdminTorcidaDetailView(PlatformAdminAPIView):
    """Edição e exclusão protegida de comunidades pelo administrador global."""

    def patch(self, request, torcida_id):
        self.check_admin(request)
        torcida = Torcida.objects.filter(pk=torcida_id).first()
        if torcida is None:
            return Response({"detail": "Torcida não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        allowed = {"nome", "slug", "escudo_url", "cor_principal"}
        data = {key: value for key, value in request.data.items() if key in allowed}
        if not data:
            return Response({"detail": "Nenhum campo válido foi enviado."}, status=status.HTTP_400_BAD_REQUEST)
        if "nome" in data:
            if not isinstance(data["nome"], str) or not data["nome"].strip():
                return Response({"detail": "Informe um nome válido."}, status=status.HTTP_400_BAD_REQUEST)
            data["nome"] = data["nome"].strip()[:120]
        if "slug" in data:
            import re
            slug = re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]", "-", str(data["slug"]).strip().lower())).strip("-")
            if not slug or len(slug) > 140:
                return Response({"detail": "Identificador inválido."}, status=status.HTTP_400_BAD_REQUEST)
            if Torcida.objects.filter(slug=slug).exclude(pk=torcida.pk).exists():
                return Response({"detail": "Este identificador já está em uso."}, status=status.HTTP_400_BAD_REQUEST)
            data["slug"] = slug
        if "cor_principal" in data:
            import re
            if not isinstance(data["cor_principal"], str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", data["cor_principal"]):
                return Response({"detail": "A cor deve estar no formato hexadecimal, como #202020."}, status=status.HTTP_400_BAD_REQUEST)
        for key, value in data.items():
            setattr(torcida, key, value)
        torcida.save(update_fields=list(data.keys()))
        return Response({"id": torcida.pk, "nome": torcida.nome, "slug": torcida.slug, "escudo_url": torcida.escudo_url, "cor_principal": torcida.cor_principal, "detail": "Torcida atualizada com sucesso."})

    def delete(self, request, torcida_id):
        self.check_admin(request)
        torcida = Torcida.objects.filter(pk=torcida_id).first()
        if torcida is None:
            return Response({"detail": "Torcida não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        membros = torcida.membros.count()
        publicacoes = torcida.publicacoes.count()
        if membros or publicacoes:
            return Response({"detail": f"Exclusão bloqueada: esta torcida possui {membros} integrante(s) e {publicacoes} publicação(ões). Remova ou transfira esses vínculos antes."}, status=status.HTTP_409_CONFLICT)
        nome = torcida.nome
        torcida.delete()
        return Response({"detail": f'Torcida "{nome}" excluída.'}, status=status.HTTP_200_OK)


class PlatformAdminTorcidaMemberView(PlatformAdminAPIView):
    """Gestão global de responsáveis e integrantes de uma torcida."""

    def patch(self, request, torcida_id, membro_id):
        self.check_admin(request)
        torcida = Torcida.objects.filter(pk=torcida_id).first()
        if torcida is None:
            return Response({"detail": "Torcida não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            membro = Membro.objects.select_for_update().select_related("usuario").filter(pk=membro_id, torcida=torcida).first()
            if membro is None:
                return Response({"detail": "Integrante não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            papel = request.data.get("papel")
            validos = [Membro.Papel.ADMIN, Membro.Papel.MODERADOR, Membro.Papel.MEMBRO]
            if papel not in validos:
                return Response({"detail": "Papel inválido. Use admin, moderador ou membro."}, status=status.HTTP_400_BAD_REQUEST)
            if membro.papel == Membro.Papel.ADMIN and papel != Membro.Papel.ADMIN:
                admins = Membro.objects.select_for_update().filter(torcida=torcida, papel=Membro.Papel.ADMIN).count()
                if admins <= 1:
                    return Response({"detail": "A torcida precisa manter pelo menos um administrador responsável."}, status=status.HTTP_409_CONFLICT)
            membro.papel = papel
            membro.save(update_fields=["papel"])
        return Response({"id": membro.pk, "usuario": membro.usuario_id, "username": membro.usuario.username, "papel": membro.papel, "detail": "Responsabilidade atualizada com sucesso."})

    def delete(self, request, torcida_id, membro_id):
        self.check_admin(request)
        torcida = Torcida.objects.filter(pk=torcida_id).first()
        if torcida is None:
            return Response({"detail": "Torcida não encontrada."}, status=status.HTTP_404_NOT_FOUND)
        with transaction.atomic():
            membro = Membro.objects.select_for_update().filter(pk=membro_id, torcida=torcida).first()
            if membro is None:
                return Response({"detail": "Integrante não encontrado."}, status=status.HTTP_404_NOT_FOUND)
            if membro.papel == Membro.Papel.ADMIN:
                admins = Membro.objects.select_for_update().filter(torcida=torcida, papel=Membro.Papel.ADMIN).count()
                if admins <= 1:
                    return Response({"detail": "Não é possível remover o último administrador responsável pela torcida."}, status=status.HTTP_409_CONFLICT)
            membro.delete()
        return Response({"detail": "Integrante removido da torcida."}, status=status.HTTP_200_OK)
