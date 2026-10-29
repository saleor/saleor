import django_filters
from django.db.models import Count, Exists, OuterRef, Q, QuerySet, Subquery
from django.db.models.functions import Coalesce

from ...account.models import Address, CustomerType, User
from ...attribute.models import (
    AssignedUserAttributeValue,
    AttributeCustomerType,
    AttributeValue,
)
from ...core.search import prefix_search
from ...order.models import Order
from ..attribute.shared_filters import (
    AssignedAttributeWhereInput,
    filter_objects_by_attributes,
    validate_attribute_value_input,
)
from ..core.descriptions import ADDED_IN_323
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
from ..core.filters.where_filters import (
    ListObjectTypeWhereFilter,
    MetadataWhereBase,
    OperationObjectTypeWhereFilter,
)
from ..core.filters.where_input import (
    FilterInputDescriptions,
    GlobalIDFilterInput,
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
from ..utils import resolve_global_ids_to_primary_keys
from ..utils.filters import (
    filter_by_id,
    filter_by_ids,
    filter_range_field,
    filter_where_by_range_field,
    filter_where_by_value_field,
    filter_where_range_field_with_conditions,
)
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
    return prefix_search(qs, value)


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


def filter_customer_type_search(qs, _, value):
    if not value:
        return qs
    return qs.filter(Q(name__trigram_similar=value) | Q(slug__trigram_similar=value))


class CustomerTypeWhere(MetadataWhereBase):
    ids = GlobalIDMultipleChoiceWhereFilter(method=filter_by_ids("CustomerType"))
    name = ObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_name",
        help_text="Filter by customer type name.",
    )
    slug = ObjectTypeWhereFilter(
        input_class=StringFilterInput,
        method="filter_slug",
        help_text="Filter by customer type slug.",
    )
    is_default = BooleanWhereFilter(
        method="filter_is_default",
        help_text="Filter by whether the customer type is the default one.",
    )

    @staticmethod
    def filter_name(qs, _, value):
        return filter_where_by_value_field(qs, "name", value)

    @staticmethod
    def filter_slug(qs, _, value):
        return filter_where_by_value_field(qs, "slug", value)

    @staticmethod
    def filter_is_default(qs, _, value):
        if value is None:
            return qs.none()
        return qs.filter(is_default=value)


class CustomerTypeWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_USERS
        filterset_class = CustomerTypeWhere


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


def _get_assigned_user_attribute_for_attribute_value(
    attribute_values: QuerySet[AttributeValue],
    db_connection_name: str,
):
    """Build an expression matching users by assigned attribute values.

    Values of attributes that are not assigned to the user's customer type
    are skipped, as such values are not exposed on the user. Users without
    an explicitly assigned customer type belong to the default one.
    """
    default_customer_type_id = Subquery(
        CustomerType.objects.using(db_connection_name)
        .filter(is_default=True)
        .values("id")[:1]
    )
    attribute_assigned_to_customer_type = AttributeCustomerType.objects.using(
        db_connection_name
    ).filter(
        attribute_id=OuterRef("value__attribute_id"),
        customer_type_id=Coalesce(
            OuterRef(OuterRef("customer_type_id")), default_customer_type_id
        ),
    )
    return Q(
        Exists(
            AssignedUserAttributeValue.objects.using(db_connection_name).filter(
                Exists(attribute_values.filter(id=OuterRef("value_id"))),
                Exists(attribute_assigned_to_customer_type),
                user_id=OuterRef("id"),
            )
        )
    )


def filter_users_by_attributes(qs, value):
    return filter_objects_by_attributes(
        qs,
        value,
        _get_assigned_user_attribute_for_attribute_value,
    )


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
    customer_type = OperationObjectTypeWhereFilter(
        input_class=GlobalIDFilterInput,
        method="filter_customer_type",
        help_text=(
            "Filter by customer type. Filtering by the default customer type "
            "also matches users without an explicitly assigned customer type."
            + ADDED_IN_323
        ),
    )
    attributes = ListObjectTypeWhereFilter(
        input_class=AssignedAttributeWhereInput,
        method="filter_attributes",
        help_text="Filter by attributes associated with the customer." + ADDED_IN_323,
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

    @staticmethod
    def filter_customer_type(qs, _, value):
        if not value:
            return qs.none()
        if eq := value.get("eq"):
            _, pks = resolve_global_ids_to_primary_keys([eq], "CustomerType", True)
        elif one_of := value.get("one_of"):
            _, pks = resolve_global_ids_to_primary_keys(one_of, "CustomerType", True)
        else:
            return qs.none()
        lookup = Q(customer_type_id__in=pks)
        if (
            CustomerType.objects.using(qs.db)
            .filter(is_default=True, pk__in=pks)
            .exists()
        ):
            # Users without an explicitly assigned customer type belong to the
            # default one.
            lookup |= Q(customer_type_id__isnull=True)
        return qs.filter(lookup)

    @staticmethod
    def filter_attributes(qs, _, value):
        if not value:
            return qs.none()
        return filter_users_by_attributes(qs, value)

    def is_valid(self):
        if attributes := self.data.get("attributes"):
            validate_attribute_value_input(attributes, self.queryset.db)
        return super().is_valid()


class CustomerWhereInput(WhereInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_USERS
        filterset_class = CustomerWhereFilterInput


class PermissionGroupFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(method=filter_search)
    ids = GlobalIDMultipleChoiceFilter(method="filter_ids")

    @staticmethod
    def filter_ids(qs, _, value):
        from . import types as account_types

        return filter_by_id(account_types.Group)(qs, _, value)


class StaffUserFilter(django_filters.FilterSet):
    status = EnumFilter(input_class=StaffMemberStatus, method=filter_staff_status)
    search = django_filters.CharFilter(method=filter_user_search)
    ids = GlobalIDMultipleChoiceFilter(method="filter_ids")
    # TODO - Figure out after permission types
    # department = ObjectTypeFilter

    class Meta:
        model = User
        fields = ["status", "search"]

    @staticmethod
    def filter_ids(qs, _, value):
        from . import types as account_types

        return filter_by_id(account_types.User)(qs, _, value)
