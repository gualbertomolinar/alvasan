from rest_framework.routers import DefaultRouter

router = DefaultRouter()

from pedidos.views import PedidosViewSet
from django.urls import path


router.register(r'', PedidosViewSet, basename='pedidos')

urlpatterns = router.urls