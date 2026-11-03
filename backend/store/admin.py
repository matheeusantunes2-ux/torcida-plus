from django.contrib import admin
from .models import Produto, Pedido, ItemPedido, ItemCarrinho
@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
 list_display=("nome","torcida","categoria","preco","quantidade","ativo")
 list_filter=("torcida","categoria","ativo")
 search_fields=("nome","descricao")
class ItemPedidoInline(admin.TabularInline):
 model=ItemPedido; extra=0; readonly_fields=("nome_produto","preco_unitario","quantidade","total")
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
 list_display=("id","torcida","comprador","status","total","criado_em")
 list_filter=("torcida","status"); inlines=[ItemPedidoInline]
admin.site.register(ItemCarrinho)
