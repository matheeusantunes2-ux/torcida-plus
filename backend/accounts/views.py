from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions

from .models import Perfil
from .serializers import CadastroSerializer, PerfilSerializer


class CadastroView(generics.CreateAPIView):
    serializer_class = CadastroSerializer
    permission_classes = [permissions.AllowAny]


class MeuPerfilView(generics.RetrieveUpdateAPIView):
    serializer_class = PerfilSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        perfil, _ = Perfil.objects.get_or_create(
            usuario=self.request.user
        )
        return perfil


class PerfilPublicoView(generics.RetrieveAPIView):
    serializer_class = PerfilSerializer
    permission_classes = [permissions.AllowAny]

    def get_object(self):
        return get_object_or_404(
            Perfil.objects.select_related("usuario"),
            usuario__username=self.kwargs["username"],
        )
