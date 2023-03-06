import graphene

from ..core.descriptions import DEPRECATED_IN_3X_INPUT
from ..core.types import SortInputObjectType


class ExportFileSortField(graphene.Enum):
    STATUS = ["status"]
    CREATED_AT = ["created_at"]
    UPDATED_AT = ["updated_at"]
    LAST_MODIFIED_AT = ["updated_at"]

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            ExportFileSortField.STATUS.name: "status.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            ExportFileSortField.CREATED_AT.name: "creation date.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            ExportFileSortField.UPDATED_AT.name: (  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
                f"update date. {DEPRECATED_IN_3X_INPUT}"
            ),
            ExportFileSortField.LAST_MODIFIED_AT.name: "update date.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
        }

        for self.name in ExportFileSortField.__enum__._member_names_:
            return f"Sort export file by {descriptions[self.name]}"
        raise ValueError(f"Unsupported enum value: {self.value}")


class ExportFileSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = ExportFileSortField
        type_name = "export file"
