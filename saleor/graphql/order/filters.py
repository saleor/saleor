import django_filters

from ...order.models import Order
from ..core.filters import EnumFilter, ListObjectTypeFilter, ObjectTypeFilter
from ..core.types.common import DateRangeInput
from ..payment.enums import PaymentChargeStatusEnum
from ..utils import filter_by_query_param
from .enums import CustomOrderStatusFilter, OrderStatusFilter


def filter_payment_status(qs, _, value):
    if value:
        qs = qs.filter(
            payments__is_active=True, payments__charge_status__in=value)
    return qs


def filter_custom_status(qs, _, value):
    if value:
        if value == CustomOrderStatusFilter.READY_TO_FULFILL:
            qs = qs.ready_to_fulfill()
        elif value == CustomOrderStatusFilter.READY_TO_CAPTURE:
            qs = qs.ready_to_capture()
    return qs


def filter_status(qs, _, value):
    if value:
        qs = qs.filter(status__in=value)
    return qs


def filter_customer(qs, _, value):
    customer_fields = [
        'user_email',
        'user__first_name',
        'user__last_name',
        'user__email',
    ]
    qs = filter_by_query_param(qs, value, customer_fields)
    return qs


def filter_created_range(qs, _, value):
    gte, lte = value.get('gte'), value.get('lte')
    if gte:
        qs = qs.filter(created__date__gte=gte)
    if lte:
        qs = qs.filter(created__date__lte=lte)
    return qs


class DraftOrderFilter(django_filters.FilterSet):
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_created_range
    )

    class Meta:
        model = Order
        fields = ['customer', 'created']


class OrderFilter(DraftOrderFilter):
    payment_status = ListObjectTypeFilter(
        input_class=PaymentChargeStatusEnum, method=filter_payment_status
    )
    status = ListObjectTypeFilter(
        input_class=OrderStatusFilter, method=filter_status
    )
    custom_status = EnumFilter(
        input_class=CustomOrderStatusFilter, method=filter_custom_status
    )
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_created_range
    )

    class Meta:
        model = Order
        fields = [
            'payment_status', 'status', 'customer', 'created', 'custom_status']
