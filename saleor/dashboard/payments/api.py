from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.filters import DjangoFilterBackend, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet

from ...order.models import Payment

ERRORS = ['error', 'reject', 'rejected']
SUCCESSES = ['accept', 'confirmed', 'fully-paid', 'shipped', 'refunded']

class PaymentSerializer(serializers.ModelSerializer):
    total_price = SerializerMethodField()
    gateway_translation = SerializerMethodField()
    dashboard_order_url = SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    status_css_class = serializers.SerializerMethodField()

    class Meta:
        model = Payment

    def get_total_price(self, obj):
        total = obj.get_total_price()
        price = {name: str(value) for name, value in total._asdict().items()}
        del price['history']
        return price

    def get_gateway_translation(self, obj):
        return _("Gateway")

    def get_dashboard_order_url(self, obj):
        return reverse('dashboard:order-details',
                       kwargs={'order_pk': obj.order.id})

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_status_css_class(self, obj):
        label_cls = 'default'
        if obj.status in ERRORS:
            label_cls = 'danger'
        elif obj.status in SUCCESSES:
            label_cls = 'success'
        return label_cls


class PaymentPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 30


class PaymentViewSet(ModelViewSet):
    model = Payment
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter,)
    filter_fields = ('status',)
    ordering_fields = ('id', 'created', 'variant', 'status', 'user')
    pagination_class = PaymentPagination

    def get_queryset(self):
        queryset = super(PaymentViewSet, self).get_queryset()
        return queryset
