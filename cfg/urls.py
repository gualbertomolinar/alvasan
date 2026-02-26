from rest_framework.routers import DefaultRouter

router = DefaultRouter()

from .views import SyncViewSet
from django.urls import path


router.register(r'', SyncViewSet, basename='cfg')

urlpatterns = router.urls