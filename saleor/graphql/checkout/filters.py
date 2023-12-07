from uuid import UUID

import django_filters
from django.db.models import Exists, OuterRef, Q

from ...account.models import User
from ...checkout.models import Checkout
from ...payment.models import Payment
from ..channel.filters import get_currency_from_filter_data
from ..channel.types import Channel
from ..core.doc_category import DOC_CATEGORY_CHECKOUT
from ..core.filters import (
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
    OperationObjectTypeWhereFilter,
    WhereFilterSet,
)
from ..core.types import DateRangeInput, FilterInputObjectType
from ..core.types.filter_input import DecimalFilterInput
from ..core.utils import from_global_id_or_error
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import filter_range_field
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
        payments = Payment.objects.filter(pk=payment_id).values("id")
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
    users = User.objects.filter(
        Q(email__ilike=value) | Q(first_name__ilike=value) | Q(last_name__ilike=value)
    ).values("pk")

    return qs.filter(Q(Exists(users.filter(id=OuterRef("user_id")))))


def filter_channels(qs, _, values):
    if values:
        _, channels_ids = resolve_global_ids_to_primary_keys(values, Channel)
        qs = qs.filter(channel_id__in=channels_ids)
    return qs


def filter_checkout_search(qs, _, value):
    if payment_id := get_payment_id_from_query(value):
        return filter_checkout_by_payment(qs, payment_id)

    users = User.objects.filter(
        Q(email__ilike=value) | Q(first_name__ilike=value) | Q(last_name__ilike=value)
    ).values("pk")

    filter_option = Q(Exists(users.filter(id=OuterRef("user_id"))))

    possible_token = get_checkout_id_from_query(value) or value

    if checkout_id := get_checkout_token_from_query(possible_token):
        filter_option |= Q(token=checkout_id)

    payments = Payment.objects.filter(psp_reference=value).values("id")
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


class CheckoutDiscountedObjectWhere(WhereFilterSet):
    total_price = OperationObjectTypeWhereFilter(
        input_class=DecimalFilterInput,
        method="filter_total_price",
        field_name="filter_total_price",
        help_text="Filter by the checkout total price.",
    )

    class Meta:
        model = Checkout
        fields = ["total_price"]

    def filter_total_price(self, queryset, name, value):
        currency = get_currency_from_filter_data(self.data)
        return _filter_total_price(queryset, name, value, currency)


def _filter_total_price(qs, _, value, currency):
    # We will have single channel/currency as the rule can applied only
    # on channels with the same currencies
    # TODO: maybe we should have `currency` as a filter argument instead
    # of `channel_slug`?

    # TODO: handle `oneOf` as well
    range = value.get("range")
    if not range:
        return qs._meta.model.objects.none()

    # TODO: raise a ValidationError if `currency` is not provided
    total_price_lte = range.get("lte")
    total_price_gte = range.get("gte")
    # qs could contains all orders from all channels with given currencies
    # so we cannot filter by channel
    # from other side - this method is per channel and a setting deciding
    # if price entered with taxes included or not is per channel

    # TODO: this is temporary solution - we should use gross or net, depending on
    # order channel tax configuration - prices_entered_with_tax
    if total_price_gte:
        qs = qs.filter(
            currency=currency,
            total_gross_amount__gte=total_price_gte,
        )
    if total_price_lte:
        qs = qs.filter(
            currency=currency,
            total_gross_amount__lte=total_price_lte,
        )
    return qs
