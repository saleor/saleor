import graphene

from ..core.doc_category import DOC_CATEGORY_APPS
from ..core.types import SortInputObjectType
from ..directives import doc


@doc(category=DOC_CATEGORY_APPS)
class AppSortField(graphene.Enum):
    NAME = ["name", "pk"]
    CREATION_DATE = ["created_at", "name", "pk"]

    @property
    def description(self):
        if self.name in AppSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort apps by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


@doc(category=DOC_CATEGORY_APPS)
class AppSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = AppSortField
        type_name = "apps"
