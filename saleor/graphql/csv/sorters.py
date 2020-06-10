import graphene

from ..core.types import SortInputObjectType


class ExportFileSortField(graphene.Enum):
    STATUS = ["status"]
    CREATED_AT = ["created_at"]
    UPDATED_AT = ["updated_at"]

    @property
    def description(self):
        if self.name in ExportFileSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort export file by {sort_name}."
        raise ValueError("Unsupported enum value: %s" % self.value)


class ExportFileSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = ExportFileSortField
        type_name = "export file"
