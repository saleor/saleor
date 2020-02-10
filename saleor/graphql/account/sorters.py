import graphene
from django.db.models import Count, QuerySet

from ..core.types import SortInputObjectType


class ServiceAccountSortField(graphene.Enum):
    NAME = "name"
    CREATION_DATE = "created"

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            ServiceAccountSortField.NAME,
            ServiceAccountSortField.CREATION_DATE,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort service accounts by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class ServiceAccountSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = ServiceAccountSortField
        type_name = "service accounts"


class UserSortField(graphene.Enum):
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    EMAIL = "email"
    ORDER_COUNT = "order_count"

    @property
    def description(self):
        # pylint: disable=no-member
        if self in [
            UserSortField.FIRST_NAME,
            UserSortField.LAST_NAME,
            UserSortField.EMAIL,
            UserSortField.ORDER_COUNT,
        ]:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort users by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)

    @staticmethod
    def sort_by_order_count(
        queryset: QuerySet, sort_by: SortInputObjectType
    ) -> QuerySet:
        return queryset.annotate(order_count=Count("orders__id")).order_by(
            f"{sort_by.direction}order_count", "email"
        )


class UserSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = UserSortField
        type_name = "users"


class PermissionGroupSortField(graphene.Enum):
    NAME = "name"

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
