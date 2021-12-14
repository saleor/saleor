import django_filters
from django.db.models import Exists, IntegerField, OuterRef, Q, Sum
from django.db.models.functions import Cast
from django.utils import timezone
from graphene_django.filter import GlobalIDMultipleChoiceFilter

from ...giftcard import GiftCardEvents
from ...giftcard.models import GiftCardEvent
from ...order.models import Order, OrderLine
from ...order.search import search_orders
from ...product.models import ProductVariant
from ..core.filters import ListObjectTypeFilter, MetadataFilterBase, ObjectTypeFilter
from ..core.types.common import DateRangeInput
from ..core.utils import from_global_id_or_error
from ..payment.enums import PaymentChargeStatusEnum
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import filter_range_field
from .enums import OrderStatusFilter


def filter_payment_status(qs, _, value):
    if value:
        qs = qs.filter(payments__is_active=True, payments__charge_status__in=value)
    return qs


def get_payment_id_from_query(value):
    try:
        return from_global_id_or_error(value, only_type="Payment")[1]
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
        query_objects |= qs.ready_to_capture()

    return qs & query_objects


def filter_customer(qs, _, value):
    qs = qs.filter(
        Q(user_email__ilike=value)
        | Q(user__email__trigram_similar=value)
        | Q(user__first_name__trigram_similar=value)
        | Q(user__last_name__trigram_similar=value)
    )
    return qs


def filter_created_range(qs, _, value):
    return filter_range_field(qs, "created__date", value)


def filter_order_search(qs, _, value):
    return search_orders(qs, value)


def filter_channels(qs, _, values):
    if values:
        _, channels_ids = resolve_global_ids_to_primary_keys(values, "Channel")
        qs = qs.filter(channel_id__in=channels_ids)
    return qs


def filter_is_click_and_collect(qs, _, values):
    if values is not None:
        lookup = Q(collection_point__isnull=False) | Q(
            collection_point_name__isnull=False
        )
        qs = qs.filter(lookup) if values is True else qs.exclude(lookup)
    return qs


def filter_is_preorder(qs, _, values):
    if values is not None:
        variants = ProductVariant.objects.filter(
            Q(is_preorder=True)
            & (
                Q(preorder_end_date__isnull=True)
                | Q(preorder_end_date__gte=timezone.now())
            )
        ).values("id")
        lines = OrderLine.objects.filter(
            Exists(variants.filter(id=OuterRef("variant_id")))
        )
        lookup = Exists(lines.filter(order_id=OuterRef("id")))
        qs = qs.filter(lookup) if values is True else qs.exclude(lookup)
    return qs


def filter_order_ids(qs, _, values):
    if values:
        _, order_ids = resolve_global_ids_to_primary_keys(values, "Order")
        qs = qs.filter(id__in=order_ids)
    return qs


def filter_gift_card_used(qs, _, value):
    return filter_by_gift_card(qs, value, GiftCardEvents.USED_IN_ORDER)


def filter_gift_card_bought(qs, _, value):
    return filter_by_gift_card(qs, value, GiftCardEvents.BOUGHT)


def filter_by_gift_card(qs, value, gift_card_type):
    gift_card_events = GiftCardEvent.objects.filter(type=gift_card_type).values(
        order_id=Cast("parameters__order_id", IntegerField())
    )
    lookup = Exists(gift_card_events.filter(order_id=OuterRef("id")))
    return qs.filter(lookup) if value is True else qs.exclude(lookup)


class DraftOrderFilter(MetadataFilterBase):
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
    is_click_and_collect = django_filters.BooleanFilter(
        method=filter_is_click_and_collect
    )
    is_preorder = django_filters.BooleanFilter(method=filter_is_preorder)
    ids = GlobalIDMultipleChoiceFilter(method=filter_order_ids)
    gift_card_used = django_filters.BooleanFilter(method=filter_gift_card_used)
    gift_card_bought = django_filters.BooleanFilter(method=filter_gift_card_bought)

    class Meta:
        model = Order
        fields = ["payment_status", "status", "customer", "created", "search"]
