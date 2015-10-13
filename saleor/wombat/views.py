from ..order import Order
from ..product.models import Product
from rest_framework import generics
from .serializers import OrderSerializer, ProductSerializer


class OrderList(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer


class ProductList(generics.ListAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
