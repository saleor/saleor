from django.utils.translation import ugettext as _
from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from rest_framework.filters import DjangoFilterBackend, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.viewsets import ModelViewSet

from ...order.models import Order

ERRORS = ['error', 'reject', 'rejected']
SUCCESSES = ['accept', 'confirmed', 'fully-paid', 'shipped', 'refunded']

class OrderSerializer(serializers.ModelSerializer):
    total = SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    status_css_class = serializers.SerializerMethodField()
    last_payment_status_display = serializers.SerializerMethodField()
    last_payment_css_class = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()
    created_display = serializers.SerializerMethodField()

    class Meta:
        model = Order

    def get_total(self, obj):
        total = obj.get_total()
        price = {name: str(value) for name, value in total._asdict().items()}
        del price['history']
        return price

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_status_css_class(self, obj):
        label_cls = 'default'
        if obj.status in ERRORS:
            label_cls = 'danger'
        elif obj.status in SUCCESSES:
            label_cls = 'success'
        return label_cls

    def get_last_payment_status_display(self, obj):
        return obj.get_last_payment_status_display()

    def get_last_payment_css_class(self, obj):
        label_cls = 'default'
        last_payment = obj.payments.last()
        if last_payment.status in ERRORS:
            label_cls = 'danger'
        elif last_payment.status in SUCCESSES:
            label_cls = 'success'
        return label_cls

    def get_user(self, obj):
        user = obj.user
        if user:
            return obj.user.email
        return _('Guest')

    def get_created_display(self, obj):
        return obj.created


class OrderPagination(PageNumberPagination):
    page_size = 30
    page_size_query_param = 'page_size'
    max_page_size = 30


class OrderViewSet(ModelViewSet):
    model = Order
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = (DjangoFilterBackend, OrderingFilter,)
    filter_fields = ('status', 'shipping_method',)
    ordering_fields = ('id', 'status', 'created', 'user', 'total')
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = super(OrderViewSet, self).get_queryset()
        queryset = queryset.prefetch_related('user')
        return queryset
