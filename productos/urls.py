from rest_framework.routers import DefaultRouter

router = DefaultRouter()

from productos.views import ListaPrecioViewSet, ProductosViewSet
from django.urls import path


router.register(r'lista', ListaPrecioViewSet, basename='lista')
router.register(r'', ProductosViewSet, basename='productos')

urlpatterns = router.urls
