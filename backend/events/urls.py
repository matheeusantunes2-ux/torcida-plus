from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import EventoViewSet, IngressoEventoView

router = DefaultRouter()
router.register("", EventoViewSet, basename="evento")
urlpatterns = [path("<int:evento_id>/ingresso/", IngressoEventoView.as_view(), name="evento-ingresso")] + router.urls
