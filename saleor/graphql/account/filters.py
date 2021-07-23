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
        UserAddress = User.addresses.through
        addresses = Address.objects.filter(
            Q(first_name__ilike=value)
            | Q(last_name__ilike=value)
            | Q(city__ilike=value)
            | Q(country__ilike=value)
            | Q(phone=value)
        ).values("id")
        user_addresses = UserAddress.objects.filter(
            Exists(addresses.filter(pk=OuterRef("address_id")))
        ).values("user_id")
        qs = qs.filter(
            Q(email__ilike=value)
            | Q(first_name__ilike=value)
            | Q(last_name__ilike=value)
            | Q(Exists(user_addresses.filter(user_id=OuterRef("pk"))))
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
