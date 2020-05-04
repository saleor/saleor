import graphene

from ...core.types import SortInputObjectType


class ServiceAccountSortField(graphene.Enum):
    NAME = ["name", "pk"]
    CREATION_DATE = ["created", "name", "pk"]

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
