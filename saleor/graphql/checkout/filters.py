from uuid import UUID

import django_filters
from django.db.models import Exists, OuterRef, Q

from ...account.models import User
from ...checkout.models import Checkout
from ...payment.models import Payment
from ..channel.types import Channel
from ..core.filters import (
    GlobalIDMultipleChoiceFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
)
from ..core.types import DateRangeInput, FilterInputObjectType
from ..core.utils import from_global_id_or_error
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import filter_range_field


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


class CheckoutFilter(MetadataFilterBase):
    customer = django_filters.CharFilter(method=filter_customer)
    created = ObjectTypeFilter(input_class=DateRangeInput, method=filter_created_range)
    search = django_filters.CharFilter(method=filter_checkout_search)
    channels = GlobalIDMultipleChoiceFilter(method=filter_channels)

    class Meta:
        model = Checkout
        fields = ["customer", "created", "search"]


class CheckoutFilterInput(FilterInputObjectType):
    class Meta:
        filterset_class = CheckoutFilter
