from django.urls import include, path
from rest_framework.routers import DefaultRouter

from products.views import ProductViewSet

router = DefaultRouter()
router.register(r"productos", ProductViewSet, basename="producto")

urlpatterns = [
    path("", include(router.urls)),
]
