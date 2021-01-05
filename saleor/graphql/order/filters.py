import django_filters
from django.db.models import Sum
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from ...order.models import Order
from ..channel.types import Channel
from ..core.filters import ListObjectTypeFilter, ObjectTypeFilter
from ..core.types.common import DateRangeInput
from ..core.utils import from_global_id_strict_type
from ..payment.enums import PaymentChargeStatusEnum
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import filter_by_query_param, filter_range_field
from .enums import OrderStatusFilter


def filter_payment_status(qs, _, value):
    if value:
        qs = qs.filter(payments__is_active=True, payments__charge_status__in=value)
    return qs


def get_payment_id_from_query(value):
    try:
        return from_global_id_strict_type(value, only_type="Payment", field="pk")
    except Exception:
        return None


def filter_order_by_payment(qs, payment_id):
    if payment_id:
        qs = qs.filter(payments__pk=payment_id)
    return qs


def filter_status(qs, _, value):
    query_objects = qs.none()

    if value:
        query_objects |= qs.filter(status__in=value)

    if OrderStatusFilter.READY_TO_FULFILL in value:
        # to use & between queries both of them need to have applied the same
        # annotate
        qs = qs.annotate(amount_paid=Sum("payments__captured_amount"))
        query_objects |= qs.ready_to_fulfill()

    if OrderStatusFilter.READY_TO_CAPTURE in value:
        qs = qs.distinct()
        query_objects = query_objects.distinct()
        query_objects |= qs.ready_to_capture()

    return qs & query_objects


def filter_customer(qs, _, value):
    customer_fields = [
        "user_email",
        "user__first_name",
        "user__last_name",
        "user__email",
    ]
    qs = filter_by_query_param(qs, value, customer_fields)
    return qs


def filter_created_range(qs, _, value):
    return filter_range_field(qs, "created__date", value)


def filter_order_search(qs, _, value):
    order_fields = [
        "pk",
        "discount_name",
        "translated_discount_name",
        "user_email",
        "user__first_name",
        "user__last_name",
        "payments__transactions__searchable_key",
    ]
    payment_id = get_payment_id_from_query(value)
    if payment_id:
        return filter_order_by_payment(qs, payment_id)

    qs = filter_by_query_param(qs, value, order_fields)
    return qs


def filter_channels(qs, _, values):
    if values:
        _, channels_ids = resolve_global_ids_to_primary_keys(values, Channel)
        qs = qs.filter(channel_id__in=channels_ids)
    return qs


class DraftOrderFilter(django_filters.FilterSet):
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(input_class=DateRangeInput, method=filter_created_range)
    search = django_filters.CharFilter(method=filter_order_search)
    channels = GlobalIDMultipleChoiceFilter(method=filter_channels)

    class Meta:
        model = Order
        fields = ["customer", "created", "search"]


class OrderFilter(DraftOrderFilter):
    payment_status = ListObjectTypeFilter(
        input_class=PaymentChargeStatusEnum, method=filter_payment_status
    )
    status = ListObjectTypeFilter(input_class=OrderStatusFilter, method=filter_status)
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(input_class=DateRangeInput, method=filter_created_range)
    search = django_filters.CharFilter(method=filter_order_search)
    channels = GlobalIDMultipleChoiceFilter(method=filter_channels)

    class Meta:
        model = Order
        fields = ["payment_status", "status", "customer", "created", "search"]
