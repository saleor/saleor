from uuid import UUID

import django_filters
import graphene
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from graphql.error import GraphQLError

from ...giftcard import GiftCardEvents
from ...giftcard.models import GiftCardEvent
from ...order.models import Order, OrderLine
from ...order.search import search_orders
from ...payment import ChargeStatus
from ...product.models import ProductVariant
from ..channel.filters import get_currency_from_filter_data
from ..core.filters import (
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
)
from ..core.types import DateRangeInput, DateTimeRangeInput
from ..core.utils import from_global_id_or_error
from ..discount.filters import DiscountedObjectWhere
from ..payment.enums import PaymentChargeStatusEnum
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import filter_range_field, filter_where_by_numeric_field
from .enums import OrderAuthorizeStatusEnum, OrderChargeStatusEnum, OrderStatusFilter


def filter_payment_status(qs, _, value):
    if value:
        lookup = Q(payments__is_active=True, payments__charge_status__in=value)
        if ChargeStatus.FULLY_REFUNDED in value:
            lookup |= Q(payments__charge_status=ChargeStatus.FULLY_REFUNDED)
        qs = qs.filter(lookup)
    return qs


def filter_authorize_status(qs, _, value):
    if value:
        qs = qs.filter(authorize_status__in=value)
    return qs


def filter_charge_status(qs, _, value):
    if value:
        qs = qs.filter(charge_status__in=value)
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
    return filter_range_field(qs, "created_at__date", value)


def filter_updated_at_range(qs, _, value):
    return filter_range_field(qs, "updated_at", value)


def filter_order_search(qs, _, value):
    return search_orders(qs, value)


def filter_channels(qs, _, values):
    if values:
        _, channels_ids = resolve_global_ids_to_primary_keys(values, "Channel")
        qs = qs.filter(channel_id__in=channels_ids)
    return qs


def filter_checkouts(qs, _, values):
    if values:
        _, checkout_ids = resolve_global_ids_to_primary_keys(values, "Checkout")
        qs = qs.filter(checkout_token__in=checkout_ids)
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
        variants = (
            ProductVariant.objects.using(qs.db)
            .filter(
                Q(is_preorder=True)
                & (
                    Q(preorder_end_date__isnull=True)
                    | Q(preorder_end_date__gte=timezone.now())
                )
            )
            .values("id")
        )
        lines = OrderLine.objects.using(qs.db).filter(
            Exists(variants.filter(id=OuterRef("variant_id")))
        )
        lookup = Exists(lines.filter(order_id=OuterRef("id")))
        qs = qs.filter(lookup) if values is True else qs.exclude(lookup)
    return qs


def filter_gift_card_used(qs, _, value):
    return filter_by_gift_card(qs, value, GiftCardEvents.USED_IN_ORDER)


def filter_gift_card_bought(qs, _, value):
    return filter_by_gift_card(qs, value, GiftCardEvents.BOUGHT)


def filter_by_gift_card(qs, value, gift_card_type):
    gift_card_events = (
        GiftCardEvent.objects.using(qs.db)
        .filter(type=gift_card_type)
        .values("order_id")
    )
    lookup = Exists(gift_card_events.filter(order_id=OuterRef("id")))
    return qs.filter(lookup) if value is True else qs.exclude(lookup)


def filter_order_by_id(qs, _, value):
    if not value:
        return qs
    _, obj_pks = resolve_global_ids_to_primary_keys(value, "Order")
    pks = []
    old_pks = []
    for pk in obj_pks:
        try:
            pks.append(UUID(pk))
        except ValueError:
            old_pks.append(pk)
    return qs.filter(Q(id__in=pks) | (Q(use_old_id=True) & Q(number__in=old_pks)))


def filter_by_order_number(qs, _, values):
    if not values:
        return qs
    return qs.filter(number__in=values)


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
    authorize_status = ListObjectTypeFilter(
        input_class=OrderAuthorizeStatusEnum, method=filter_authorize_status
    )
    charge_status = ListObjectTypeFilter(
        input_class=OrderChargeStatusEnum, method=filter_charge_status
    )
    status = ListObjectTypeFilter(input_class=OrderStatusFilter, method=filter_status)
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(input_class=DateRangeInput, method=filter_created_range)
    updated_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_updated_at_range
    )
    search = django_filters.CharFilter(method=filter_order_search)
    channels = GlobalIDMultipleChoiceFilter(method=filter_channels)
    is_click_and_collect = django_filters.BooleanFilter(
        method=filter_is_click_and_collect
    )
    is_preorder = django_filters.BooleanFilter(method=filter_is_preorder)
    ids = GlobalIDMultipleChoiceFilter(method=filter_order_by_id)
    gift_card_used = django_filters.BooleanFilter(method=filter_gift_card_used)
    gift_card_bought = django_filters.BooleanFilter(method=filter_gift_card_bought)
    numbers = ListObjectTypeFilter(
        input_class=graphene.String, method=filter_by_order_number
    )
    checkout_ids = GlobalIDMultipleChoiceFilter(method=filter_checkouts)

    class Meta:
        model = Order
        fields = ["payment_status", "status", "customer", "created", "search"]

    def is_valid(self):
        if "ids" in self.data and "numbers" in self.data:
            raise GraphQLError(
                message="'ids' and 'numbers` are not allowed to use together in filter."
            )
        return super().is_valid()


class OrderDiscountedObjectWhere(DiscountedObjectWhere):
    class Meta:
        model = Order
        fields = ["subtotal_net_amount", "total_net_amount"]

    def filter_base_subtotal_price(self, queryset, name, value):
        currency = get_currency_from_filter_data(self.data)
        return _filter_price(queryset, name, "subtotal_net_amount", value, currency)

    def filter_base_total_price(self, queryset, name, value):
        currency = get_currency_from_filter_data(self.data)
        return _filter_price(queryset, name, "total_net_amount", value, currency)


def _filter_price(qs, _, field_name, value, currency):
    # We will have single channel/currency as the rule can be applied only
    # on channels with the same currencies
    if not currency:
        raise ValidationError(
            "You must provide a currency to filter by price field.", code="required"
        )
    qs = qs.filter(currency=currency)
    return filter_where_by_numeric_field(qs, field_name, value)
