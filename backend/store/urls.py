from rest_framework.routers import DefaultRouter

from .views import ProdutoViewSet

router = DefaultRouter()
router.register("produtos", ProdutoViewSet, basename="produto")

urlpatterns = router.urls

