import graphene
from django.db.models import Count, QuerySet

from ..core.doc_category import DOC_CATEGORY_USERS
from ..core.types import SortInputObjectType
from ..directives import doc


@doc(category=DOC_CATEGORY_USERS)
class UserSortField(graphene.Enum):
    FIRST_NAME = ["first_name", "last_name", "pk"]
    LAST_NAME = ["last_name", "first_name", "pk"]
    EMAIL = ["email"]
    ORDER_COUNT = ["order_count", "email"]
    CREATED_AT = ["date_joined", "pk"]
    LAST_MODIFIED_AT = ["updated_at", "pk"]

    @property
    def description(self):
        if self.name in UserSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort users by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")

    @staticmethod
    def qs_with_order_count(queryset: QuerySet, *, channel_slug=None) -> QuerySet:
        return queryset.annotate(order_count=Count("orders__id"))


@doc(category=DOC_CATEGORY_USERS)
class UserSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = UserSortField
        type_name = "users"


@doc(category=DOC_CATEGORY_USERS)
class PermissionGroupSortField(graphene.Enum):
    """Sorting options for permission groups."""

    NAME = ["name"]

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [PermissionGroupSortField.NAME]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort permission group accounts by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


@doc(category=DOC_CATEGORY_USERS)
class PermissionGroupSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = PermissionGroupSortField
        type_name = "permission group"
