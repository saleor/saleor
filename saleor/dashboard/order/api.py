from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.filters import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet

from ...order.models import Order


class OrderSerializer(serializers.ModelSerializer):
    total = SerializerMethodField()

    class Meta:
        model = Order

    def get_total(self, obj):
        total = obj.get_total()
        price = {name: str(value) for name, value in total._asdict().items()}
        del price['history']
        return price


class OrderViewSet(ModelViewSet):
    model = Order
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('status', 'shipping_method')
    ordering_fields = ('status', 'shipping_method')
