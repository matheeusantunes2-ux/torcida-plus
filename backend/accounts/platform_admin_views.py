from django.contrib.auth import get_user_model
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
