from django.db.models import Q
from ..order import Order
from ..product.models import Product
from rest_framework import generics
from rest_framework.decorators import api_view, authentication_classes
from rest_framework.exceptions import ParseError
from rest_framework import status
from rest_framework.response import Response
from .serializers import OrderSerializer, ProductSerializer, GetWebhookRequestSerializer
from .authentication import WombatAuthentication


class OrderList(generics.ListAPIView):
    queryset = Order.objects.prefetch_related(
        'groups', 'groups__items', 'payments').select_related(
        'billing_address', 'shipping_address', 'user')
    serializer_class = OrderSerializer


class ProductList(generics.ListAPIView):
    queryset = Product.objects.prefetch_related('variants',
                                                'variants__stock',
                                                'images',
                                                'attributes')
    serializer_class = ProductSerializer


@api_view(['POST'])
@authentication_classes((WombatAuthentication,))
def get_orders_webhook(request):
    serializer = GetWebhookRequestSerializer(data=request.data)
    if not serializer.is_valid():
        raise ParseError()
    request_id = serializer.data.get('request_id')
    parameters = serializer.data.get('parameters', {})
    since = parameters.get('since')
    id = parameters.get('id')
    query_filter = None

    if since:
        query_filter = Q(last_status_change__gte=since)
    if id:
        query_filter = Q(pk=id)

    if not query_filter:
        raise ParseError()

    orders = OrderList.queryset.filter(query_filter)
    serialized_orders = OrderSerializer(orders, many=True)

    data = {
        'request_id': request_id,
        'orders': serialized_orders.data
    }

    return Response(data=data, status=status.HTTP_200_OK)

