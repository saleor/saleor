import graphene

from ..core.types import SortInputObjectType


class ExportFileSortField(graphene.Enum):
    STATUS = ["status"]
    CREATED_AT = ["created_at"]
    UPDATED_AT = ["updated_at"]
    LAST_MODIFIED_AT = ["updated_at", "pk"]

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            ExportFileSortField.STATUS.name: "status.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            ExportFileSortField.CREATED_AT.name: "creation date.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            ExportFileSortField.UPDATED_AT.name: "update date.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            ExportFileSortField.LAST_MODIFIED_AT.name: "update date.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
        }

        for self.name in ExportFileSortField.__enum__._member_names_:
            return f"Sort export file by {descriptions[self.name]}"
        raise ValueError(f"Unsupported enum value: {self.value}")

    @property
    def deprecation_reason(self):
        deprecations = {
            ExportFileSortField.UPDATED_AT.name: "Use `LAST_MODIFIED_AT` instead.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
        }
        if self.name in deprecations:
            return deprecations[self.name]
        return None


class ExportFileSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = ExportFileSortField
        type_name = "export file"
