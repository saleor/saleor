import django_filters
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Case, Count, OuterRef, Q, Subquery, When
from django.db.models.functions import Coalesce, Greatest

from ...account.models import Address, User
from ..core.filters import EnumFilter, MetadataFilterBase, ObjectTypeFilter
from ..core.types.common import DateRangeInput, IntRangeInput
from ..utils.filters import filter_range_field
from .enums import StaffMemberStatus

SEARCH_RESULT_TRESHOLD = 0.3


def filter_date_joined(qs, _, value):
    return filter_range_field(qs, "date_joined__date", value)


def filter_number_of_orders(qs, _, value):
    qs = qs.annotate(total_orders=Count("orders"))
    return filter_range_field(qs, "total_orders", value)


def filter_placed_orders(qs, _, value):
    return filter_range_field(qs, "orders__created__date", value)


def filter_staff_status(qs, _, value):
    if value == StaffMemberStatus.ACTIVE:
        return qs.filter(is_staff=True, is_active=True)
    if value == StaffMemberStatus.DEACTIVATED:
        return qs.filter(is_staff=True, is_active=False)
    return qs


def filter_user_search(qs, _, value):
    if value:
        UserAddress = User.addresses.through
        addresses = (
            Address.objects.annotate(
                addresses_rank=Greatest(
                    TrigramSimilarity("first_name", value),
                    TrigramSimilarity("last_name", value),
                    TrigramSimilarity("city", value),
                    TrigramSimilarity("country", value),
                    Case(
                        When(phone=value, then=1.0),
                        default=0.0,
                    ),
                )
            )
            .filter(Q(addresses_rank__gte=SEARCH_RESULT_TRESHOLD))
            .values("addresses_rank")
        )
        user_addresses = (
            UserAddress.objects.annotate(
                user_addresses_rank=Coalesce(
                    Subquery(addresses.filter(pk=OuterRef("address_id"))), 0.0
                )
            )
            .order_by("-user_addresses_rank")
            .values("user_addresses_rank")
        )
        qs = (
            qs.annotate(
                rank=Greatest(
                    TrigramSimilarity("email", value),
                    TrigramSimilarity("first_name", value),
                    TrigramSimilarity("last_name", value),
                    Subquery(user_addresses.filter(user_id=OuterRef("pk"))[:1]),
                )
            )
            .filter(Q(rank__gte=SEARCH_RESULT_TRESHOLD))
            .order_by("-rank", "id")
        )
    return qs


def filter_search(qs, _, value):
    if value:
        qs = qs.filter(name__trigram_similar=value)
    return qs


class CustomerFilter(MetadataFilterBase):
    date_joined = ObjectTypeFilter(
        input_class=DateRangeInput, method=filter_date_joined
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


class StaffUserFilter(django_filters.FilterSet):
    status = EnumFilter(input_class=StaffMemberStatus, method=filter_staff_status)
    search = django_filters.CharFilter(method=filter_user_search)

    # TODO - Figure out after permision types
    # department = ObjectTypeFilter

    class Meta:
        model = User
        fields = ["status", "search"]
