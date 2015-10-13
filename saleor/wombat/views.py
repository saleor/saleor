from ..order import Order
from rest_framework import generics
from .serializers import OrderSerializer


class OrderList(generics.ListAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
