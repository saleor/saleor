import decimal
from typing import List

import django_filters
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from ...discount import DiscountValueType
from ...discount.models import Sale, SaleChannelListing, Voucher, VoucherQueryset
from ..core.filters import (
    GlobalIDMultipleChoiceFilter,
    ListObjectTypeFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
)
from ..core.types import DateTimeRangeInput, IntRangeInput
from ..utils.filters import filter_by_id, filter_range_field
from .enums import DiscountStatusEnum, DiscountValueTypeEnum, VoucherDiscountType


def filter_status(
    qs: VoucherQueryset, _, value: List[DiscountStatusEnum]
) -> VoucherQueryset:
    if not value:
        return qs
    query_objects = qs.none()
    now = timezone.now()
    if DiscountStatusEnum.ACTIVE in value:
        query_objects |= qs.active(now)
    if DiscountStatusEnum.EXPIRED in value:
        query_objects |= qs.expired(now)
    if DiscountStatusEnum.SCHEDULED in value:
        query_objects |= qs.filter(start_date__gt=now)
    return qs & query_objects


def filter_times_used(qs, _, value):
    return filter_range_field(qs, "used", value)


def filter_discount_type(
    qs: VoucherQueryset, _, values: List[VoucherDiscountType]
) -> VoucherQueryset:
    if values:
        query = Q()
        if VoucherDiscountType.FIXED in values:
            query |= Q(
                discount_value_type=VoucherDiscountType.FIXED.value  # type: ignore
            )
        if VoucherDiscountType.PERCENTAGE in values:
            query |= Q(
                discount_value_type=VoucherDiscountType.PERCENTAGE.value  # type: ignore
            )  # type: ignore
        if VoucherDiscountType.SHIPPING in values:
            query |= Q(type=VoucherDiscountType.SHIPPING.value)  # type: ignore
        qs = qs.filter(query)
    return qs


def filter_started(qs, _, value):
    return filter_range_field(qs, "start_date", value)


def filter_sale_type(qs, _, value):
    if value in [DiscountValueType.FIXED, DiscountValueType.PERCENTAGE]:
        qs = qs.filter(type=value)
    return qs


def filter_sale_search(qs, _, value):
    try:
        value = decimal.Decimal(value)
    except decimal.DecimalException:
        return qs.filter(Q(name__ilike=value) | Q(type__ilike=value))
    channel_listings = SaleChannelListing.objects.filter(discount_value=value).values(
        "pk"
    )
    return qs.filter(Exists(channel_listings.filter(sale_id=OuterRef("pk"))))


def filter_voucher_search(qs, _, value):
    return qs.filter(Q(name__ilike=value) | Q(code__ilike=value))


def filter_updated_at_range(qs, _, value):
    return filter_range_field(qs, "updated_at", value)


class VoucherFilter(MetadataFilterBase):
    status = ListObjectTypeFilter(input_class=DiscountStatusEnum, method=filter_status)
    times_used = ObjectTypeFilter(input_class=IntRangeInput, method=filter_times_used)

    discount_type = ListObjectTypeFilter(
        input_class=VoucherDiscountType, method=filter_discount_type
    )
    started = ObjectTypeFilter(input_class=DateTimeRangeInput, method=filter_started)
    search = django_filters.CharFilter(method=filter_voucher_search)
    ids = GlobalIDMultipleChoiceFilter(method=filter_by_id("Voucher"))

    class Meta:
        model = Voucher
        fields = ["status", "times_used", "discount_type", "started", "search"]


class SaleFilter(MetadataFilterBase):
    status = ListObjectTypeFilter(input_class=DiscountStatusEnum, method=filter_status)
    sale_type = ObjectTypeFilter(
        input_class=DiscountValueTypeEnum, method=filter_sale_type
    )
    started = ObjectTypeFilter(input_class=DateTimeRangeInput, method=filter_started)
    updated_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_updated_at_range
    )
    search = django_filters.CharFilter(method=filter_sale_search)

    class Meta:
        model = Sale
        fields = ["status", "sale_type", "started", "search"]
