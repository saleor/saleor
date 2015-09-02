from rest_framework import routers

from order.api import OrderViewSet


router = routers.DefaultRouter()
router.register(r'orders', OrderViewSet)
