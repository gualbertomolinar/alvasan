from rest_framework.routers import DefaultRouter

router = DefaultRouter()

from ventas.views import VentasViewSet
from django.urls import path


router.register(r'', VentasViewSet, basename='ventas')


urlpatterns = router.urls