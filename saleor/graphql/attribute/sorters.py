from ..core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ..core.types import BaseEnum, SortInputObjectType


class AttributeSortField(BaseEnum):
    NAME = ["name", "slug"]
    SLUG = ["slug"]
    VALUE_REQUIRED = ["value_required", "name", "slug"]
    IS_VARIANT_ONLY = ["is_variant_only", "name", "slug"]
    VISIBLE_IN_STOREFRONT = ["visible_in_storefront", "name", "slug"]

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            AttributeSortField.NAME.name: "Sort attributes by name",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            AttributeSortField.SLUG.name: "Sort attributes by slug",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            AttributeSortField.VALUE_REQUIRED.name: (  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
                "Sort attributes by the value required flag"
            ),
            AttributeSortField.IS_VARIANT_ONLY.name: (  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
                "Sort attributes by the variant only flag"
            ),
            AttributeSortField.VISIBLE_IN_STOREFRONT.name: (  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
                "Sort attributes by visibility in the storefront"
            ),
        }
        if self.name in descriptions:
            return descriptions[self.name]
        raise ValueError(f"Unsupported enum value: {self.value}")


class AttributeSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES
        sort_enum = AttributeSortField
        type_name = "attributes"


class AttributeChoicesSortField(BaseEnum):
    NAME = ["name", "slug"]
    SLUG = ["slug"]

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES

    @property
    def description(self):
        descriptions = {
            AttributeChoicesSortField.NAME.name: "Sort attribute choice by name.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            AttributeChoicesSortField.SLUG.name: "Sort attribute choice by slug.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
        }
        if self.name in descriptions:
            return descriptions[self.name]
        raise ValueError(f"Unsupported enum value: {self.value}")


class AttributeChoicesSortingInput(SortInputObjectType):
    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES
        sort_enum = AttributeChoicesSortField
        type_name = "attribute choices"
