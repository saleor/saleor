from ..core.doc_category import DOC_CATEGORY_TAXES
from ..core.types import BaseEnum, SortInputObjectType


class TaxClassSortField(BaseEnum):
    NAME = ["name", "pk"]

    class Meta:
        doc_category = DOC_CATEGORY_TAXES

    @property
    def description(self):
        if self.name in TaxClassSortField.__enum__._member_names_:
            sort_name = self.name.lower().replace("_", " ")
            return f"Sort tax classes by {sort_name}."
        raise ValueError(f"Unsupported enum value: {self.value}")


class TaxClassSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_TAXES
        sort_enum = TaxClassSortField
        type_name = "tax classes"
