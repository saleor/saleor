import graphene
from django.db.models import Count, QuerySet
from graphql.error import GraphQLError

from ..core.types import SortInputObjectType


class UserSortField(graphene.Enum):
    FIRST_NAME = ["first_name", "last_name", "pk"]
    LAST_NAME = ["last_name", "first_name", "pk"]
    EMAIL = ["email"]
    ORDER_COUNT = ["order_count", "email"]
    RANK = ["rank"]

    @property
    def description(self):
        descriptions = {
            UserSortField.RANK.name: (
                "rank. Note: This option is available only with the `search` filter."
            ),
        }
        sort_name = None
        if self.name in descriptions:
            sort_name = {descriptions[self.name]}
        if self.name in UserSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
        if sort_name:
            return f"Sort users by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def qs_with_order_count(queryset: QuerySet, **_kwargs) -> QuerySet:
        return queryset.annotate(order_count=Count("orders__id"))

    @staticmethod
    def qs_with_rank(queryset: QuerySet, **_kwargs) -> QuerySet:
        if "rank" in queryset.query.annotations.keys():
            return queryset
        raise GraphQLError("Sorting by Rank is available only with searching.")


class UserSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = UserSortField
        type_name = "users"


class PermissionGroupSortField(graphene.Enum):
    NAME = ["name"]

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [PermissionGroupSortField.NAME]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort permission group accounts by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class PermissionGroupSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = PermissionGroupSortField
        type_name = "permission group"
