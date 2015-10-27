from rest_framework import routers

from .customer.api import CustomerViewSet
from .order.api import OrderViewSet
from .payments.api import PaymentViewSet

router = routers.DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'payments', PaymentViewSet)
router.register(r'orders', OrderViewSet)
