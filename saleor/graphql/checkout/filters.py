from uuid import UUID

import django_filters
from django.core.exceptions import ValidationError
from django.db.models import Exists, OuterRef, Q

from ...account.models import User
from ...checkout.models import Checkout
from ...payment.models import Payment
from ..channel.filters import get_currency_from_filter_data
from ..channel.types import Channel
from ..core.doc_category import DOC_CATEGORY_CHECKOUT
from ..core.filters import (
    FilterInputObjectType,
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
)
from ..core.types import DateRangeInput
from ..core.utils import from_global_id_or_error
from ..discount.filters import DiscountedObjectWhere
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import filter_range_field, filter_where_by_numeric_field
from .enums import CheckoutAuthorizeStatusEnum, CheckoutChargeStatusEnum


def get_checkout_token_from_query(value):
    try:
        return UUID(value, version=4)
    except ValueError:
        # If it's a value error, then the string
        # is not a valid hex code for a UUID.
        return None


def get_payment_id_from_query(value):
    try:
        return from_global_id_or_error(value, only_type="Payment")[1]
    except Exception:
        return None


def get_checkout_id_from_query(value):
    try:
        return from_global_id_or_error(value, only_type="Checkout")[1]
    except Exception:
        return None


def filter_checkout_by_payment(qs, payment_id):
    if payment_id:
        payments = Payment.objects.using(qs.db).filter(pk=payment_id).values("id")
        qs = qs.filter(Q(Exists(payments.filter(checkout_id=OuterRef("token")))))
    return qs


def filter_created_range(qs, _, value):
    return filter_range_field(qs, "created_at__date", value)


def filter_authorize_status(qs, _, value):
    if value:
        qs = qs.filter(authorize_status__in=value)
    return qs


def filter_charge_status(qs, _, value):
    if value:
        qs = qs.filter(charge_status__in=value)
    return qs


def filter_updated_at_range(qs, _, value):
    return filter_range_field(qs, "last_change__date", value)


def filter_customer(qs, _, value):
    users = (
        User.objects.using(qs.db)
        .filter(
            Q(email__ilike=value)
            | Q(first_name__ilike=value)
            | Q(last_name__ilike=value)
        )
        .values("pk")
    )

    return qs.filter(Q(Exists(users.filter(id=OuterRef("user_id")))))


def filter_channels(qs, _, values):
    if values:
        _, channels_ids = resolve_global_ids_to_primary_keys(values, Channel)
        qs = qs.filter(channel_id__in=channels_ids)
    return qs


def filter_checkout_search(qs, _, value):
    if payment_id := get_payment_id_from_query(value):
        return filter_checkout_by_payment(qs, payment_id)

    users = (
        User.objects.using(qs.db)
        .filter(
            Q(email__ilike=value)
            | Q(first_name__ilike=value)
            | Q(last_name__ilike=value)
        )
        .values("pk")
    )

    filter_option = Q(Exists(users.filter(id=OuterRef("user_id"))))

    possible_token = get_checkout_id_from_query(value) or value

    if checkout_id := get_checkout_token_from_query(possible_token):
        filter_option |= Q(token=checkout_id)

    payments = Payment.objects.using(qs.db).filter(psp_reference=value).values("id")
    filter_option |= Q(Exists(payments.filter(checkout_id=OuterRef("token"))))

    return qs.filter(filter_option)


def filter_checkout_metadata(qs, _, value):
    for metadata_item in value:
        if metadata_item.value:
            qs = qs.filter(
                metadata_storage__metadata__contains={
                    metadata_item.key: metadata_item.value
                }
            )
        else:
            qs = qs.filter(metadata_storage__metadata__has_key=metadata_item.key)
    return qs


class CheckoutFilter(MetadataFilterBase):
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(input_class=DateRangeInput, method=filter_created_range)
    search = django_filters.CharFilter(method=filter_checkout_search)
    channels = GlobalIDMultipleChoiceFilter(method=filter_channels)
    metadata = ListObjectTypeFilter(
        input_class=MetadataFilter, method=filter_checkout_metadata
    )
    updated_at = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_updated_at_range
    )
    authorize_status = ListObjectTypeFilter(
        input_class=CheckoutAuthorizeStatusEnum, method=filter_authorize_status
    )
    charge_status = ListObjectTypeFilter(
        input_class=CheckoutChargeStatusEnum, method=filter_charge_status
    )

    class Meta:
        model = Checkout
        fields = ["customer", "created", "search"]


class CheckoutFilterInput(FilterInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_CHECKOUT
        filterset_class = CheckoutFilter


class CheckoutDiscountedObjectWhere(DiscountedObjectWhere):
    class Meta:
        model = Checkout
        fields = ["base_subtotal_price", "base_total_price"]

    def filter_base_subtotal_price(self, queryset, name, value):
        currency = get_currency_from_filter_data(self.data)
        return _filter_price(queryset, name, "base_subtotal_amount", value, currency)

    def filter_base_total_price(self, queryset, name, value):
        currency = get_currency_from_filter_data(self.data)
        return _filter_price(queryset, name, "base_total_amount", value, currency)


def _filter_price(qs, _, field_name, value, currency):
    # We will have single channel/currency as the rule can applied only
    # on channels with the same currencies
    if not currency:
        raise ValidationError(
            "You must provide a currency to filter by price field.", code="required"
        )
    qs = qs.filter(currency=currency)
    return filter_where_by_numeric_field(qs, field_name, value)
