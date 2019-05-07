from datetime import date

import django_filters

from ...discount import DiscountValueType
from ...discount.models import Sale, Voucher
from ..core.filters import EnumFilter, ObjectTypeFilter
from ..core.types.common import DateRangeInput, IntRangeInput
from ..utils import filter_by_query_param
from .enums import (
    DiscountStatusEnum, DiscountValueTypeEnum, VoucherDiscountType)


def filter_status(qs, _, value):
    today = date.today()
    if value == DiscountStatusEnum.ACTIVE:
        return qs.active(today)
    if value == DiscountStatusEnum.EXPIRED:
        return qs.expired(today)
    if value == DiscountStatusEnum.SCHEDULED:
        return qs.filter(start_date__gt=today)
    return qs


def filter_times_used(qs, _, value):
    gte = value.get('gte')
    lte = value.get('lte')
    if gte:
        qs = qs.filter(used__gte=gte)
    if lte:
        qs = qs.filter(used__lte=lte)
    return qs


def filter_discount_type(qs, _, value):
    if value in [VoucherDiscountType.PERCENTAGE, VoucherDiscountType.FIXED]:
        qs = qs.filter(discount_value_type=value)
    elif value == VoucherDiscountType.SHIPPING:
        qs = qs.filter(type=value)
    return qs


def filter_started(qs, _, value):
    gte = value.get('gte')
    lte = value.get('lte')
    if gte:
        qs = qs.filter(start_date__gte=gte)
    if lte:
        qs = qs.filter(start_date__gte=lte)
    return qs


def filter_sale_type(qs, _, value):
    if value in [DiscountValueType.FIXED, DiscountValueType.PERCENTAGE]:
        qs = qs.filter(type=value)
    return qs


def filter_sale_search(qs, _, value):
    search_fields = ('name', 'value', 'type')
    if value:
        qs = filter_by_query_param(qs, value, search_fields)
    return qs


def filter_voucher_search(qs, _, value):
    search_fields = ('name', 'code')
    if value:
        qs = filter_by_query_param(qs, value, search_fields)
    return qs


class VoucherFilter(django_filters.FilterSet):
    status = EnumFilter(input_class=DiscountStatusEnum, method=filter_status)
    times_used = ObjectTypeFilter(
        input_class=IntRangeInput, method=filter_times_used
    )

    discount_type = EnumFilter(
        input_class=VoucherDiscountType, method=filter_discount_type
    )
    started = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_started
    )
    search = django_filters.CharFilter(method=filter_voucher_search)

    class Meta:
        model = Voucher
        fields = ['status', 'times_used', 'discount_type', 'started', 'search']


class SaleFilter(django_filters.FilterSet):
    status = ObjectTypeFilter(
        input_class=DiscountStatusEnum, method=filter_status)
    sale_type = ObjectTypeFilter(
        input_class=DiscountValueTypeEnum, method=filter_sale_type)
    started = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_started)
    search = django_filters.CharFilter(method=filter_sale_search)

    class Meta:
        model = Sale
        fields = ['status', 'sale_type', 'started', 'search']
