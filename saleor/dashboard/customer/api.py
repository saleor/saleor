from django.core.urlresolvers import reverse
from django.db.models import Count, Max
from rest_framework import serializers
from rest_framework.filters import DjangoFilterBackend, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet

from ...userprofile.models import User


class CustomerSerializer(serializers.ModelSerializer):

    num_orders = serializers.IntegerField()
    last_order_id = serializers.IntegerField()
    dashboard_last_order_url = serializers.SerializerMethodField()
    dashboard_customer_url = serializers.SerializerMethodField()
    default_shipping_address__first_name = serializers.CharField(source='default_shipping_address.first_name')
    default_shipping_address__last_name = serializers.CharField(source='default_shipping_address.last_name')
    default_shipping_address__city = serializers.CharField(source='default_shipping_address.city')
    default_shipping_address__country = serializers.SerializerMethodField()

    def get_dashboard_last_order_url(self, customer):
        return reverse('dashboard:order-details',
                       kwargs={'order_pk': customer.last_order_id})

    def get_dashboard_customer_url(self, customer):
        return reverse('dashboard:customer-details',
                       kwargs={'pk': customer.id})

    def get_default_shipping_address__country(self, customer):
        return customer.default_shipping_address.get_country_display()

    class Meta:
        model = User
        exclude = ('password',)


class CustomerPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 30

class CustomerViewSet(ModelViewSet):

    model = User
    serializer_class = CustomerSerializer
    queryset = User.objects.all()
    filter_backends = (DjangoFilterBackend, OrderingFilter)
    filter_fields = ('is_active', 'email')
    ordering_fields = ('id', 'email', 'default_shipping_address__first_name',
                       'default_shipping_address__last_name',
                       'default_shipping_address__city',
                       'default_shipping_address__country',
                       'last_order_id',
                       'num_orders',)
    pagination_class = CustomerPagination

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
