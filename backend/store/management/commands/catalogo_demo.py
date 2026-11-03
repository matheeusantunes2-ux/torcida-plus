from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from torcidas.models import Torcida
from store.models import Produto
ITEMS=[("Camisa oficial","Vestuário","Camisa demonstrativa em tecido esportivo.",79.90,30),("Camisa treino","Vestuário","Modelo leve para treino.",69.90,25),("Boné bordado","Acessórios","Boné com bordado frontal.",39.90,20),("Cachecol","Acessórios","Cachecol em tecido macio.",49.90,18),("Bandeira média","Bandeiras","Bandeira decorativa para encontros.",59.90,12),("Caneca personalizada","Casa","Caneca demonstrativa.",29.90,40),("Copo térmico","Casa","Copo térmico de demonstração.",54.90,15),("Chaveiro","Acessórios","Chaveiro emborrachado.",14.90,60),("Kit adesivos","Acessórios","Kit com cinco adesivos.",9.90,100),("Mochila","Bolsas","Mochila casual para eventos.",89.90,10)]
class Command(BaseCommand):
 help="Cria dez produtos fictícios para uma torcida."
 def add_arguments(self,p):p.add_argument("--torcida",type=int,required=True)
 def handle(self,*a,**o):
  try:t=Torcida.objects.get(pk=o["torcida"])
  except Torcida.DoesNotExist:raise CommandError("Torcida não encontrada.")
  n=0
  for nome,cat,desc,preco,qtd in ITEMS:
   _,created=Produto.objects.get_or_create(torcida=t,nome=nome,defaults={"categoria":cat,"descricao":desc,"preco":Decimal(str(preco)),"quantidade":qtd});n+=created
  self.stdout.write(self.style.SUCCESS(f"{n} produtos adicionados à loja de {t.nome}."))
