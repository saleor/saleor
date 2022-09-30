import django_filters
from django.db.models import Count

from ...account.models import User
from ...account.search import search_users
from ..core.descriptions import ADDED_IN_38
from ..core.filters import (
    EnumFilter,
    GlobalIDMultipleChoiceFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
)
from ..core.types import DateRangeInput, DateTimeRangeInput, IntRangeInput
from ..utils.filters import filter_by_id, filter_range_field
from . import types as account_types
from .enums import StaffMemberStatus


def filter_date_joined(qs, _, value):
    return filter_range_field(qs, "date_joined__date", value)


def filter_updated_at(qs, _, value):
    return filter_range_field(qs, "updated_at", value)


def filter_number_of_orders(qs, _, value):
    qs = qs.annotate(total_orders=Count("orders"))
    return filter_range_field(qs, "total_orders", value)


def filter_placed_orders(qs, _, value):
    return filter_range_field(qs, "orders__created_at__date", value)


def filter_staff_status(qs, _, value):
    if value == StaffMemberStatus.ACTIVE:
        return qs.filter(is_staff=True, is_active=True)
    if value == StaffMemberStatus.DEACTIVATED:
        return qs.filter(is_staff=True, is_active=False)
    return qs


def filter_user_search(qs, _, value):
    return search_users(qs, value)


def filter_search(qs, _, value):
    if value:
        qs = qs.filter(name__trigram_similar=value)
    return qs


class CustomerFilter(MetadataFilterBase):
    ids = GlobalIDMultipleChoiceFilter(
        field_name="id", help_text=f"Filter by ids. {ADDED_IN_38}"
    )
    date_joined = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_date_joined
    )
    updated_at = ObjectTypeFilter(
        input_class=DateTimeRangeInput, method=filter_updated_at
    )
    number_of_orders = ObjectTypeFilter(
        input_class=IntRangeInput, method=filter_number_of_orders
    )
    placed_orders = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_placed_orders
    )
    search = django_filters.CharFilter(method=filter_user_search)

    class Meta:
        model = User
        fields = [
            "date_joined",
            "number_of_orders",
            "placed_orders",
            "search",
        ]


class PermissionGroupFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_search)
    ids = GlobalIDMultipleChoiceFilter(method=filter_by_id(account_types.Group))


class StaffUserFilter(django_filters.FilterSet):
    status = EnumFilter(input_class=StaffMemberStatus, method=filter_staff_status)
    search = django_filters.CharFilter(method=filter_user_search)
    ids = GlobalIDMultipleChoiceFilter(
        method=filter_by_id(
            account_types.User,
        )
    )
    # TODO - Figure out after permission types
    # department = ObjectTypeFilter

    class Meta:
        model = User
        fields = ["status", "search"]
