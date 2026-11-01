from rest_framework import generics, permissions
from .serializers import CadastroSerializer


class CadastroView(generics.CreateAPIView):
    serializer_class = CadastroSerializer
    permission_classes = [permissions.AllowAny]
