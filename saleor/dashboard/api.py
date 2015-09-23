from rest_framework import routers

from customer.api import CustomerViewSet
from order.api import OrderViewSet


router = routers.DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'orders', OrderViewSet)
