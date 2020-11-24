from typing import List

import django_filters
from django.db.models import Q
from django.utils import timezone

from ...discount import DiscountValueType
from ...discount.models import Sale, Voucher, VoucherQueryset
from ..core.filters import ListObjectTypeFilter, ObjectTypeFilter
from ..core.types.common import DateTimeRangeInput, IntRangeInput
from ..utils.filters import filter_by_query_param, filter_range_field
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
    qs: VoucherQueryset, _, value: List[VoucherDiscountType]
) -> VoucherQueryset:
    if value:
        query = Q()
        if VoucherDiscountType.FIXED in value:
            query |= Q(
                discount_value_type=VoucherDiscountType.FIXED.value  # type: ignore
            )
        if VoucherDiscountType.PERCENTAGE in value:
            query |= Q(
                discount_value_type=VoucherDiscountType.PERCENTAGE.value  # type: ignore
            )
        if VoucherDiscountType.SHIPPING in value:
            query |= Q(type=VoucherDiscountType.SHIPPING)
        qs = qs.filter(query).distinct()
    return qs


def filter_started(qs, _, value):
    return filter_range_field(qs, "start_date", value)


def filter_sale_type(qs, _, value):
    if value in [DiscountValueType.FIXED, DiscountValueType.PERCENTAGE]:
        qs = qs.filter(type=value)
    return qs


def filter_sale_search(qs, _, value):
    search_fields = ("name", "channel_listings__discount_value", "type")
    if value:
        qs = filter_by_query_param(qs, value, search_fields)
    return qs


def filter_voucher_search(qs, _, value):
    search_fields = ("name", "code")
    if value:
        qs = filter_by_query_param(qs, value, search_fields)
    return qs


class VoucherFilter(django_filters.FilterSet):
    status = ListObjectTypeFilter(input_class=DiscountStatusEnum, method=filter_status)
    times_used = ObjectTypeFilter(input_class=IntRangeInput, method=filter_times_used)

    discount_type = ListObjectTypeFilter(
        input_class=VoucherDiscountType, method=filter_discount_type
    )
    started = ObjectTypeFilter(input_class=DateTimeRangeInput, method=filter_started)
    search = django_filters.CharFilter(method=filter_voucher_search)

    class Meta:
        model = Voucher
        fields = ["status", "times_used", "discount_type", "started", "search"]


class SaleFilter(django_filters.FilterSet):
    status = ListObjectTypeFilter(input_class=DiscountStatusEnum, method=filter_status)
    sale_type = ObjectTypeFilter(
        input_class=DiscountValueTypeEnum, method=filter_sale_type
    )
    started = ObjectTypeFilter(input_class=DateTimeRangeInput, method=filter_started)
    search = django_filters.CharFilter(method=filter_sale_search)

    class Meta:
        model = Sale
        fields = ["status", "sale_type", "started", "search"]
