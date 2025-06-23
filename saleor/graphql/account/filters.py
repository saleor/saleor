import django_filters
from django.db.models import Count, Exists, OuterRef

from ...account.models import User
from ...account.search import search_users
from ...order.models import Order
from ..core.doc_category import DOC_CATEGORY_USERS
from ..core.filters import (
    EnumFilter,
    GlobalIDMultipleChoiceFilter,
    GlobalIDMultipleChoiceWhereFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
    ObjectTypeWhereFilter,
)
from ..core.filters.where_filters import MetadataWhereBase
from ..core.filters.where_input import (
    WhereInputObjectType,
)
from ..core.types import DateRangeInput, DateTimeRangeInput, IntRangeInput
from ..utils.filters import (
    filter_by_id,
    filter_by_ids,
    filter_range_field,
    filter_where_by_range_field,
)
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
    ids = GlobalIDMultipleChoiceFilter(field_name="id", help_text="Filter by ids.")
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


class CustomerWhereFilterInput(MetadataWhereBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("User"))
    date_joined = ObjectTypeWhereFilter(
        input_class=DateTimeRangeInput,
        method="filter_date_joined",
        help_text="Filter by date joined.",
    )
    updated_at = ObjectTypeWhereFilter(
        input_class=DateTimeRangeInput,
        method="filter_updated_at",
        help_text="Filter by last updated date.",
    )
    placed_orders_at = ObjectTypeWhereFilter(
        input_class=DateTimeRangeInput,
        method="filter_placed_orders_at",
        help_text="Filter by date when orders were placed.",
    )

    def filter_date_joined(self, qs, _, value):
        return filter_where_by_range_field(qs, "date_joined", value)

    def filter_updated_at(self, qs, _, value):
        return filter_where_by_range_field(qs, "updated_at", value)

    def filter_placed_orders_at(self, qs, _, value):
        if value is None:
            return qs.none()
        orders = filter_where_by_range_field(
            Order.objects.using(qs.db), "created_at", value
        )
        return qs.filter(Exists(orders.filter(user_id=OuterRef("id"))))


class CustomerWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_USERS
        filterset_class = CustomerWhereFilterInput


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
