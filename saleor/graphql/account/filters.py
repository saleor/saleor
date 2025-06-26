import django_filters
from django.db.models import Count, Exists, OuterRef

from ...account.models import Address, User
from ...account.search import search_users
from ...order.models import Order
from ..core.doc_category import DOC_CATEGORY_USERS
from ..core.filters import (
    BooleanWhereFilter,
    EnumFilter,
    GlobalIDMultipleChoiceFilter,
    GlobalIDMultipleChoiceWhereFilter,
    MetadataFilterBase,
    ObjectTypeFilter,
    ObjectTypeWhereFilter,
)
from ..core.filters.where_filters import MetadataWhereBase
from ..core.filters.where_input import (
    FilterInputDescriptions,
    IntFilterInput,
    StringFilterInput,
    WhereInputObjectType,
)
from ..core.types import (
    BaseInputObjectType,
    DateRangeInput,
    DateTimeRangeInput,
    IntRangeInput,
    NonNullList,
)
from ..utils.filters import (
    filter_by_id,
    filter_by_ids,
    filter_range_field,
    filter_where_by_range_field,
    filter_where_by_value_field,
    filter_where_range_field_with_conditions,
)
from . import types as account_types
from .enums import CountryCodeEnum, StaffMemberStatus


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


def filter_address(value):
    if not value:
        return Address.objects.none()
    address_qs = Address.objects.all()
    if (phone_number := value.get("phone_number")) is not None:
        address_qs = filter_where_by_value_field(address_qs, "phone", phone_number)
    if (country := value.get("country")) is not None:
        address_qs = filter_where_by_value_field(address_qs, "country", country)
    return address_qs


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


class CountryCodeEnumFilterInput(BaseInputObjectType):
    eq = CountryCodeEnum(description=FilterInputDescriptions.EQ, required=False)
    one_of = NonNullList(
        CountryCodeEnum,
        description=FilterInputDescriptions.ONE_OF,
        required=False,
    )
    not_one_of = NonNullList(
        CountryCodeEnum,
        description=FilterInputDescriptions.NOT_ONE_OF,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS
        description = "Filter by country code."


class AddressFilterInput(BaseInputObjectType):
    phone_number = StringFilterInput(
        help_text="Filter by phone number.",
    )
    country = CountryCodeEnumFilterInput(
        help_text="Filter by country code.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_USERS
        description = "Filtering options for addresses."


class CustomerWhereFilterInput(MetadataWhereBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("User"))
    email = ObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_email",
        help_text="Filter by email address.",
    )
    first_name = ObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_first_name",
        help_text="Filter by first name.",
    )
    last_name = ObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_last_name",
        help_text="Filter by last name.",
    )
    is_active = BooleanWhereFilter(
        field_name="is_active",
        help_text="Filter by whether the user is active.",
    )
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
    addresses = ObjectTypeWhereFilter(
        input_class=AddressFilterInput,
        method="filter_addresses",
        help_text="Filter by addresses data associated with user.",
    )
    number_of_orders = ObjectTypeWhereFilter(
        input_class=IntFilterInput,
        method="filter_number_of_orders",
        help_text="Filter by number of orders placed by the user.",
    )

    @staticmethod
    def filter_email(qs, _, value):
        return filter_where_by_value_field(qs, "email", value)

    @staticmethod
    def filter_first_name(qs, _, value):
        return filter_where_by_value_field(qs, "first_name", value)

    @staticmethod
    def filter_last_name(qs, _, value):
        return filter_where_by_value_field(qs, "last_name", value)

    @staticmethod
    def filter_is_active(qs, _, value):
        if value is None:
            return qs.none()
        return qs.filter(is_active=value)

    @staticmethod
    def filter_date_joined(qs, _, value):
        return filter_where_by_range_field(qs, "date_joined", value)

    @staticmethod
    def filter_updated_at(qs, _, value):
        return filter_where_by_range_field(qs, "updated_at", value)

    @staticmethod
    def filter_placed_orders_at(qs, _, value):
        if value is None:
            return qs.none()
        orders = filter_where_by_range_field(
            Order.objects.using(qs.db), "created_at", value
        )
        return qs.filter(Exists(orders.filter(user_id=OuterRef("id"))))

    @staticmethod
    def filter_addresses(qs, _, value):
        if not value:
            return qs.none()
        UserAddress = User.addresses.through
        address_qs = filter_address(value)
        user_address_qs = UserAddress.objects.using(qs.db).filter(
            Exists(address_qs.filter(id=OuterRef("address_id"))),
        )
        return qs.filter(Exists(user_address_qs.filter(user_id=OuterRef("id"))))

    @staticmethod
    def filter_number_of_orders(qs, _, value):
        if value is None:
            return qs.none()
        return filter_where_range_field_with_conditions(qs, "number_of_orders", value)


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
