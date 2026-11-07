from django.urls import path
from .views import ProdutosView, ProdutoDetailView, CarrinhoView, CheckoutView, PedidosView, CatalogoDemoView
urlpatterns=[
 path("catalogo-demo/",CatalogoDemoView.as_view()),
 path("produtos/",ProdutosView.as_view()),
 path("produtos/<int:pk>/",ProdutoDetailView.as_view()),
 path("carrinho/",CarrinhoView.as_view()),
 path("checkout/",CheckoutView.as_view()),
 path("pedidos/",PedidosView.as_view()),
 path("pedidos/<int:pk>/",PedidosView.as_view()),
]
