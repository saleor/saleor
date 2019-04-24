import django_filters
from django.db.models import Count, Sum

from ...account.models import User
from ..core.filters import EnumFilter, ObjectTypeFilter
from ..core.types.common import DateRangeInput, IntRangeInput, PriceRangeInput
from ..utils import filter_by_query_param
from .enums import StaffMemberStatus


def filter_date_joined(qs, _, value):
    gte, lte = value.get('gte'), value.get('lte')
    if gte:
        qs = qs.filter(date_joined__date__gte=gte)
    if lte:
        qs = qs.filter(date_joined__date__lte=lte)
    return qs


def filter_money_spent(qs, _, value):
    qs = qs.annotate(money_spent=Sum('orders__total_gross'))
    money_spent_lte, money_spent_gte = value.get('lte'), value.get('gte')
    if money_spent_lte:
        qs = qs.filter(money_spent__lte=money_spent_lte)
    if money_spent_gte:
        qs = qs.filter(money_spent__gte=money_spent_gte)
    return qs


def filter_number_of_orders(qs, _, value):
    qs = qs.annotate(total_orders=Count('orders'))
    gte, lte = value.get('gte'), value.get('lte')
    if gte:
        qs = qs.filter(total_orders__gte=gte)
    if lte:
        qs = qs.filter(total_orders__lte=lte)
    return qs


def filter_placed_orders(qs, _, value):
    gte, lte = value.get('gte'), value.get('lte')
    if gte:
        qs = qs.filter(orders__created__date__gte=gte)
    if lte:
        qs = qs.filter(orders__created__date__lte=lte)
    return qs


def filter_status(qs, _, value):
    if value == StaffMemberStatus.ACTIVE:
        qs = qs.filter(is_staff=True, is_active=True)
    elif value == StaffMemberStatus.DEACTIVATED:
        qs = qs.filter(is_staff=True, is_active=False)
    return qs


def filter_search(qs, _, value):
    search_fields = (
        'email', 'first_name', 'last_name',
        'default_shipping_address__first_name',
        'default_shipping_address__last_name',
        'default_shipping_address__city', 'default_shipping_address__country'
    )
    if value:
        qs = filter_by_query_param(qs, value, search_fields)
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
    search = django_filters.CharFilter(method=filter_search)

    class Meta:
        model = User
        fields = [
            'date_joined',
            'money_spent',
            'number_of_orders',
            'placed_orders',
            'search'
        ]


class StaffUserFilter(django_filters.FilterSet):
    status = EnumFilter(input_class=StaffMemberStatus, method=filter_status)
    search = django_filters.CharFilter(method=filter_search)

    # TODO - Figure out after permision types
    # department = ObjectTypeFilter

    class Meta:
        model = User
        fields = ['status', 'search']
