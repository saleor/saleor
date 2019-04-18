import django_filters
from django.db.models import Count, Sum

from ...account.models import User
from ..core.filters import ObjectTypeFilter
from ..core.types.common import DateRangeInput, IntRangeInput, PriceRangeInput


def filter_date_joined(qs, _, value):
    from_date = value.get("from_date")
    to_date = value.get("to_date")
    if from_date:
        qs = qs.filter(date_joined__date__gte=from_date)
    if to_date:
        qs = qs.filter(date_joined__date__lte=to_date)
    return qs


def filter_money_spent(qs, _, value):
    qs = qs.annotate(money_spent=Sum('orders__total_gross'))
    money_spent_lte = value.get('lte')
    money_spent_gte = value.get('gte')
    if money_spent_lte:
        qs = qs.filter(money_spent__lte=money_spent_lte)
    if money_spent_gte:
        qs = qs.filter(money_spent__gte=money_spent_gte)
    return qs


def filter_number_of_orders(qs, _, value):
    qs = qs.annotate(total_orders=Count('orders'))
    gte = value.get('gte')
    lte = value.get('lte')
    if gte:
        qs = qs.filter(total_orders__gte=gte)
    if lte:
        qs = qs.filter(total_orders__lte=lte)
    return qs


def filter_placed_orders(qs, _, value):
    from_date = value.get("from_date")
    to_date = value.get("to_date")
    if from_date:
        qs = qs.filter(orders__created__date__gte=from_date)
    if to_date:
        qs = qs.filter(orders__created__date__lte=to_date)
    return qs


class CustomerFilter(django_filters.FilterSet):
    date_joined = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_date_joined
    )
    money_spent = ObjectTypeFilter(
        input_class=PriceRangeInput, method=filter_money_spent
    )
    number_of_orders = ObjectTypeFilter(
        input_class=IntRangeInput, method=filter_number_of_orders
    )
    placed_orders = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_placed_orders
    )

    class Meta:
        model = User
        fields = [
            "date_joined",
            "money_spent",
            "number_of_orders",
            "placed_orders",
        ]
