from decimal import Decimal
from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from torcidas.models import Membro
from .models import Produto, ItemCarrinho, Pedido, ItemPedido
from .serializers import ProdutoSerializer, ItemCarrinhoSerializer, PedidoSerializer

def membro(user,tid): return Membro.objects.filter(usuario=user,torcida_id=tid).first()
def gerente(user,tid):
 m=membro(user,tid); return bool(m and m.papel in ("admin","moderador"))

class ProdutosView(APIView):
 permission_classes=[IsAuthenticated]
 def get(self,r):
  tid=r.query_params.get("torcida")
  if not tid or not membro(r.user,tid): return Response({"detail":"Você precisa participar desta torcida."},status=403)
  qs=Produto.objects.filter(torcida_id=tid,ativo=True)
  return Response(ProdutoSerializer(qs,many=True,context={"request":r}).data)
 def post(self,r):
  tid=r.data.get("torcida")
  if not tid or not gerente(r.user,tid): return Response({"detail":"Somente administradores e moderadores podem cadastrar produtos."},status=403)
  s=ProdutoSerializer(data=r.data,context={"request":r});s.is_valid(raise_exception=True);s.save(torcida_id=tid)
  return Response(s.data,status=201)

class ProdutoDetailView(APIView):
 permission_classes=[IsAuthenticated]
 def patch(self,r,pk):
  p=get_object_or_404(Produto,pk=pk)
  if not gerente(r.user,p.torcida_id): return Response({"detail":"Sem permissão."},status=403)
  s=ProdutoSerializer(p,data=r.data,partial=True,context={"request":r});s.is_valid(raise_exception=True);s.save();return Response(s.data)
 def delete(self,r,pk):
  p=get_object_or_404(Produto,pk=pk)
  if not gerente(r.user,p.torcida_id): return Response({"detail":"Sem permissão."},status=403)
  p.ativo=False;p.save(update_fields=["ativo","atualizado_em"]);return Response(status=204)

class CarrinhoView(APIView):
 permission_classes=[IsAuthenticated]
 def get(self,r):
  tid=r.query_params.get("torcida")
  if not tid or not membro(r.user,tid): return Response({"detail":"Torcida inválida."},status=403)
  qs=ItemCarrinho.objects.filter(usuario=r.user,produto__torcida_id=tid,produto__ativo=True).select_related("produto")
  return Response(ItemCarrinhoSerializer(qs,many=True,context={"request":r}).data)
 def post(self,r):
  p=get_object_or_404(Produto,pk=r.data.get("produto_id"),ativo=True)
  if not membro(r.user,p.torcida_id): return Response({"detail":"Você não participa desta torcida."},status=403)
  try:q=int(r.data.get("quantidade",1))
  except (TypeError,ValueError):return Response({"detail":"Quantidade inválida."},status=400)
  if q<1 or q>100:return Response({"detail":"Quantidade deve ser de 1 a 100."},status=400)
  item,created=ItemCarrinho.objects.get_or_create(usuario=r.user,produto=p,defaults={"quantidade":q})
  if not created:
   item.quantidade+=q;item.save()
  if item.quantidade>p.quantidade:
   item.delete();return Response({"detail":"Estoque insuficiente."},status=400)
  return Response(ItemCarrinhoSerializer(item,context={"request":r}).data,status=201 if created else 200)
 def delete(self,r):
  ItemCarrinho.objects.filter(pk=r.data.get("item_id"),usuario=r.user).delete();return Response(status=204)

class CheckoutView(APIView):
 permission_classes=[IsAuthenticated]
 def post(self,r):
  tid=r.data.get("torcida")
  if not tid or not membro(r.user,tid):return Response({"detail":"Torcida inválida."},status=403)
  required=["nome_destinatario","telefone","cep","endereco","numero","bairro","cidade","uf"]
  missing=[k for k in required if not str(r.data.get(k,"")).strip()]
  if missing:return Response({"detail":"Preencha: "+", ".join(missing)},status=400)
  with transaction.atomic():
   rows=list(ItemCarrinho.objects.select_for_update().filter(usuario=r.user,produto__torcida_id=tid,produto__ativo=True).select_related("produto"))
   if not rows:return Response({"detail":"Carrinho vazio."},status=400)
   total=Decimal("0.00")
   for row in rows:
    p=Produto.objects.select_for_update().get(pk=row.produto_id)
    if p.quantidade<row.quantidade:return Response({"detail":"Estoque insuficiente para "+p.nome},status=409)
    total+=p.preco*row.quantidade
   fields={k:r.data.get(k,"") for k in required+["complemento","observacoes"]}
   pedido=Pedido.objects.create(torcida_id=tid,comprador=r.user,total=total,**fields)
   for row in rows:
    p=Produto.objects.select_for_update().get(pk=row.produto_id)
    ItemPedido.objects.create(pedido=pedido,produto=p,nome_produto=p.nome,preco_unitario=p.preco,quantidade=row.quantidade,total=p.preco*row.quantidade)
    p.quantidade-=row.quantidade;p.save(update_fields=["quantidade","atualizado_em"])
   ItemCarrinho.objects.filter(pk__in=[x.pk for x in rows]).delete()
  return Response(PedidoSerializer(pedido).data,status=201)

class PedidosView(APIView):
 permission_classes=[IsAuthenticated]
 def get(self,r):
  tid=r.query_params.get("torcida")
  if not tid or not membro(r.user,tid):return Response({"detail":"Torcida inválida."},status=403)
  qs=Pedido.objects.filter(torcida_id=tid)
  if not gerente(r.user,tid):qs=qs.filter(comprador=r.user)
  return Response(PedidoSerializer(qs.prefetch_related("itens"),many=True).data)
 def patch(self,r,pk):
  p=get_object_or_404(Pedido,pk=pk)
  if not gerente(r.user,p.torcida_id):return Response({"detail":"Sem permissão."},status=403)
  if r.data.get("status") not in dict(Pedido.Status.choices):return Response({"detail":"Status inválido."},status=400)
  p.status=r.data["status"];p.save(update_fields=["status"]);return Response(PedidoSerializer(p).data)


class CatalogoDemoView(APIView):
 permission_classes=[IsAuthenticated]
 def post(self,r):
  tid=r.data.get("torcida")
  if not tid or not gerente(r.user,tid):
   return Response({"detail":"Somente administradores e moderadores podem carregar o catálogo de demonstração."},status=403)
  exemplos=[
   ("Camisa oficial","Vestuário","Camisa demonstrativa em tecido esportivo.",79.90,30),
   ("Camisa treino","Vestuário","Modelo leve para treino e dia a dia.",69.90,25),
   ("Boné bordado","Acessórios","Boné com bordado frontal demonstrativo.",39.90,20),
   ("Cachecol","Acessórios","Cachecol em tecido macio.",49.90,18),
   ("Bandeira média","Bandeiras","Bandeira decorativa para encontros.",59.90,12),
   ("Caneca personalizada","Casa","Caneca demonstrativa para colecionar.",29.90,40),
   ("Copo térmico","Casa","Copo térmico de demonstração.",54.90,15),
   ("Chaveiro","Acessórios","Chaveiro emborrachado demonstrativo.",14.90,60),
   ("Kit adesivos","Acessórios","Kit com cinco adesivos fictícios.",9.90,100),
   ("Mochila","Bolsas","Mochila casual para eventos e viagens.",89.90,10),
  ]
  criados=0
  for nome,categoria,descricao,preco,qtd in exemplos:
   _,novo=Produto.objects.get_or_create(torcida_id=tid,nome=nome,defaults={"categoria":categoria,"descricao":descricao,"preco":Decimal(str(preco)),"quantidade":qtd})
   criados+=int(novo)
  return Response({"criados":criados,"total":len(exemplos),"detail":f"{criados} produtos de demonstração adicionados."},status=201)
