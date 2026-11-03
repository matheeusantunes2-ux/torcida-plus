from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial=True
    dependencies=[
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("torcidas","0002_convitetorcida"),
    ]
    operations=[
        migrations.CreateModel(name="Produto",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("nome",models.CharField(max_length=140)),("descricao",models.TextField(blank=True)),
            ("categoria",models.CharField(default="Geral",max_length=60)),("preco",models.DecimalField(decimal_places=2,max_digits=10)),
            ("quantidade",models.PositiveIntegerField(default=0)),("imagem",models.ImageField(blank=True,null=True,upload_to="loja/produtos/")),
            ("ativo",models.BooleanField(default=True)),("criado_em",models.DateTimeField(auto_now_add=True)),("atualizado_em",models.DateTimeField(auto_now=True)),
            ("torcida",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="produtos",to="torcidas.torcida")),
        ],options={"ordering":["nome"],"indexes":[models.Index(fields=["torcida","ativo"],name="store_pro_torcida_8bd1a3_idx")]}),
        migrations.CreateModel(name="Pedido",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("status",models.CharField(choices=[("aguardando","Aguardando pagamento"),("pago","Pago"),("separacao","Em separação"),("enviado","Enviado"),("concluido","Concluído"),("cancelado","Cancelado")],default="aguardando",max_length=16)),
            ("nome_destinatario",models.CharField(max_length=140)),("telefone",models.CharField(max_length=30)),("cep",models.CharField(max_length=9)),
            ("endereco",models.CharField(max_length=180)),("numero",models.CharField(max_length=20)),("complemento",models.CharField(blank=True,max_length=100)),
            ("bairro",models.CharField(max_length=100)),("cidade",models.CharField(max_length=100)),("uf",models.CharField(max_length=2)),
            ("observacoes",models.CharField(blank=True,max_length=500)),("total",models.DecimalField(decimal_places=2,default=0,max_digits=10)),("criado_em",models.DateTimeField(auto_now_add=True)),
            ("comprador",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="pedidos_loja",to=settings.AUTH_USER_MODEL)),
            ("torcida",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="pedidos_loja",to="torcidas.torcida")),
        ],options={"ordering":["-criado_em"]}),
        migrations.CreateModel(name="ItemCarrinho",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("quantidade",models.PositiveIntegerField(default=1)),
            ("produto",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="itens_carrinho",to="store.produto")),
            ("usuario",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="itens_carrinho",to=settings.AUTH_USER_MODEL)),
        ],options={"constraints":[models.UniqueConstraint(fields=("usuario","produto"),name="carrinho_produto_unico")]}),
        migrations.CreateModel(name="ItemPedido",fields=[
            ("id",models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name="ID")),
            ("nome_produto",models.CharField(max_length=140)),("preco_unitario",models.DecimalField(decimal_places=2,max_digits=10)),
            ("quantidade",models.PositiveIntegerField()),("total",models.DecimalField(decimal_places=2,max_digits=10)),
            ("pedido",models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,related_name="itens",to="store.pedido")),
            ("produto",models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,related_name="itens_vendidos",to="store.produto")),
        ]),
    ]
