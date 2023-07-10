from django.db.models import Count, QuerySet

from ..core.doc_category import DOC_CATEGORY_USERS
from ..core.types import BaseEnum, SortInputObjectType


class UserSortField(BaseEnum):
    FIRST_NAME = ["first_name", "last_name", "pk"]
    LAST_NAME = ["last_name", "first_name", "pk"]
    EMAIL = ["email"]
    ORDER_COUNT = ["order_count", "email"]
    CREATED_AT = ["date_joined", "pk"]
    LAST_MODIFIED_AT = ["updated_at", "pk"]

    class Meta:
        doc_category = DOC_CATEGORY_USERS

    @property
    def description(self):
        if self.name in UserSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort users by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")

    @staticmethod
    def qs_with_order_count(queryset: QuerySet, *, channel_slug=None) -> QuerySet:
        return queryset.annotate(order_count=Count("orders__id"))


class UserSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_USERS
        sort_enum = UserSortField
        type_name = "users"


class PermissionGroupSortField(BaseEnum):
    NAME = ["name"]

    class Meta:
        description = "Sorting options for permission groups."
        doc_category = DOC_CATEGORY_USERS

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [PermissionGroupSortField.NAME]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort permission group accounts by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class PermissionGroupSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_USERS
        sort_enum = PermissionGroupSortField
        type_name = "permission group"
