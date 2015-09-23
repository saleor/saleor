from django.core.urlresolvers import reverse
from django.db.models import Count, Max
from rest_framework import serializers
from rest_framework.filters import DjangoFilterBackend, OrderingFilter
from rest_framework.viewsets import ModelViewSet

from ...userprofile.models import User


class CustomerSerializer(serializers.ModelSerializer):

    num_orders = serializers.IntegerField()
    last_order_id = serializers.IntegerField()
    dashboard_last_order_url = serializers.SerializerMethodField()

    def get_dashboard_last_order_url(self, customer):
        return reverse('dashboard:order-details',
                       kwargs={'order_pk': customer.last_order_id})

    class Meta:
        model = User


class CustomerViewSet(ModelViewSet):

    model = User
    serializer_class = CustomerSerializer
    queryset = User.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_fields = ('is_active',)
    ordering_fields = ('num_orders',)

    def get_queryset(self):
        queryset = super(CustomerViewSet, self).get_queryset()
        queryset = queryset.prefetch_related('orders', 'addresses')
        queryset = queryset.select_related(
            'default_billing_address', 'default_shipping_address')
        queryset = queryset.annotate(
            num_orders=Count('orders', distinct=True),
            last_order_id=Max('orders__id', distinct=True))
        queryset = queryset.exclude(num_orders=0)
        return queryset
