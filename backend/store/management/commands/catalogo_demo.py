from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from torcidas.models import Torcida
from store.models import Produto

CATALOGO=[
("Camisa oficial","Vestuário","Camisa demonstrativa da torcida, tecido esportivo.",79.90,30),
("Camisa treino","Vestuário","Modelo leve para treino e dia a dia.",69.90,25),
("Boné bordado","Acessórios","Boné com bordado frontal demonstrativo.",39.90,20),
("Cachecol","Acessórios","Cachecol de torcida em tecido macio.",49.90,18),
("Bandeira média","Bandeiras","Bandeira decorativa para encontros.",59.90,12),
("Caneca personalizada","Casa","Caneca de demonstração para colecionar.",29.90,40),
("Copo térmico","Casa","Copo térmico com identidade visual fictícia.",54.90,15),
("Chaveiro","Acessórios","Chaveiro emborrachado demonstrativo.",14.90,60),
("Adesivo kit","Acessórios","Kit com cinco adesivos fictícios.",9.90,100),
("Mochila","Bolsas","Mochila casual para eventos e viagens.",89.90,10),
]
class Command(BaseCommand):
    help="Adiciona dez produtos fictícios a uma torcida."
    def add_arguments(self,parser):parser.add_argument("--torcida",type=int,required=True)
    def handle(self,*args,**opts):
        try:t=Torcida.objects.get(pk=opts["torcida"])
        except Torcida.DoesNotExist:raise CommandError("Torcida não encontrada.")
        created=0
        for nome,categoria,descricao,preco,qtd in CATALOGO:
            _,new=Produto.objects.get_or_create(torcida=t,nome=nome,defaults={"categoria":categoria,"descricao":descricao,"preco":Decimal(str(preco)),"quantidade":qtd})
            created+=int(new)
        self.stdout.write(self.style.SUCCESS(f"{created} produtos adicionados à loja de {t.nome}."))
