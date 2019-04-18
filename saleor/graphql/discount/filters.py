from datetime import date

import django_filters

from ...discount.models import Voucher
from ..core.filters import EnumFilter, ObjectTypeFilter
from ..core.types.common import DateRangeInput, IntRangeInput
from .enums import VoucherDiscountType, VoucherStatusEnum


def filter_status(qs, _, value):
    today = date.today()
    if value == VoucherStatusEnum.ACTIVE:
        return qs.active(today)
    elif value == VoucherStatusEnum.EXPIRED:
        return qs.expired(today)
    elif value == VoucherStatusEnum.SCHEDULED:
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
    from_date = value.get('from_date')
    to_date = value.get('to_date')
    if from_date:
        qs = qs.filter(start_date__gte=from_date)
    if to_date:
        qs = qs.filter(start_date__gte=to_date)
    return qs


class VoucherFilter(django_filters.FilterSet):
    status = EnumFilter(input_class=VoucherStatusEnum, method=filter_status)
    times_used = ObjectTypeFilter(
        input_class=IntRangeInput, method=filter_times_used
    )

    discount_type = EnumFilter(
        input_class=VoucherDiscountType, method=filter_discount_type
    )
    started = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_started
    )

    class Meta:
        model = Voucher
        fields = ["status", "times_used", "discount_type", "started"]
