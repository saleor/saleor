from ..core.doc_category import DOC_CATEGORY_APPS
from ..core.types import BaseEnum, SortInputObjectType


class AppSortField(BaseEnum):
    NAME = ["name", "pk"]
    CREATION_DATE = ["created_at", "name", "pk"]

    class Meta:
        doc_category = DOC_CATEGORY_APPS

    @property
    def description(self):
        if self.name in AppSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort apps by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class AppSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_APPS
        sort_enum = AppSortField
        type_name = "apps"


class AppEventSortField(BaseEnum):
    CREATED_AT = ["created_at", "pk"]

    @property
    def description(self):
        if self.name in AppEventSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort app events by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class AppEventSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = AppEventSortField
        type_name = "events"
