from decimal import Decimal
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.permissions import is_platform_admin
from torcidas.models import Membro
from .models import Produto, ItemCarrinho, Pedido, ItemPedido
from .serializers import ProdutoSerializer, ItemCarrinhoSerializer, PedidoSerializer
from .payments import MercadoPagoError, create_preference, get_payment, validate_webhook_signature

def membro(user,tid):
 return is_platform_admin(user) or Membro.objects.filter(usuario=user,torcida_id=tid).exists()
def gerente(user,tid):
 return is_platform_admin(user) or Membro.objects.filter(usuario=user,torcida_id=tid,papel__in=("admin","moderador")).exists()
