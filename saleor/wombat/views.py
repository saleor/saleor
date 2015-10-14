from ..order import Order
from ..product.models import Product
from rest_framework import generics
from .serializers import OrderSerializer, ProductSerializer


class OrderList(generics.ListAPIView):
    queryset = Order.objects.prefetch_related(
        'groups', 'groups__items', 'payments', 'items').select_related(
        'billing_address', 'shipping_address', 'user')
    serializer_class = OrderSerializer


class ProductList(generics.ListAPIView):
    queryset = Product.objects.prefetch_related('variants',
                                                'variants__stock',
                                                'images',
                                                'attributes')
    serializer_class = ProductSerializer
