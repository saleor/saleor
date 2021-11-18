import django_filters
from django.db.models import Count, Exists, OuterRef, Q

from ...account.models import Address, User
from ..core.filters import EnumFilter, MetadataFilterBase, ObjectTypeFilter
from ..core.types.common import DateRangeInput, IntRangeInput
from ..utils.filters import filter_range_field
from .enums import StaffMemberStatus


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
        values = value.split()
        UserAddress = User.addresses.through
        addresses_filter_lookup = Q()
        for search_value in values:
            addresses_filter_lookup &= (
                Q(first_name__ilike=search_value)
                | Q(last_name__ilike=search_value)
                | Q(city__ilike=search_value)
                | Q(country__ilike=search_value)
                | Q(phone=search_value)
            )
        addresses = Address.objects.filter(addresses_filter_lookup).values("id")
        user_addresses = UserAddress.objects.filter(
            Exists(addresses.filter(pk=OuterRef("address_id")))
        ).values("user_id")

        order_filter_lookup = Q()
        for search_value in values:
            order_filter_lookup &= (
                Q(email__ilike=search_value)
                | Q(first_name__ilike=search_value)
                | Q(last_name__ilike=search_value)
            )
        order_filter_lookup |= Q(Exists(user_addresses.filter(user_id=OuterRef("pk"))))
        qs = qs.filter(order_filter_lookup)
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

    # TODO - Figure out after permission types
    # department = ObjectTypeFilter

    class Meta:
        model = User
        fields = ["status", "search"]
