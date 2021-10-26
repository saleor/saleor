import graphene

from ..core.enums import OrderDirection
from ..core.types import SortInputObjectType


class AttributeSortField(graphene.Enum):
    NAME = ["name", "slug"]
    SLUG = ["slug"]
    VALUE_REQUIRED = ["value_required", "name", "slug"]
    IS_VARIANT_ONLY = ["is_variant_only", "name", "slug"]
    VISIBLE_IN_STOREFRONT = ["visible_in_storefront", "name", "slug"]
    FILTERABLE_IN_STOREFRONT = ["filterable_in_storefront", "name", "slug"]
    FILTERABLE_IN_DASHBOARD = ["filterable_in_dashboard", "name", "slug"]
    STOREFRONT_SEARCH_POSITION = ["storefront_search_position", "name", "pk"]
    AVAILABLE_IN_GRID = ["available_in_grid", "name", "pk"]

    @property
    def description(self):
        # pylint: disable=no-member
        descriptions = {
            AttributeSortField.NAME.name: "Sort attributes by name",
            AttributeSortField.SLUG.name: "Sort attributes by slug",
            AttributeSortField.VALUE_REQUIRED.name: (
                "Sort attributes by the value required flag"
            ),
            AttributeSortField.IS_VARIANT_ONLY.name: (
                "Sort attributes by the variant only flag"
            ),
            AttributeSortField.VISIBLE_IN_STOREFRONT.name: (
                "Sort attributes by visibility in the storefront"
            ),
            AttributeSortField.FILTERABLE_IN_STOREFRONT.name: (
                "Sort attributes by the filterable in storefront flag"
            ),
            AttributeSortField.FILTERABLE_IN_DASHBOARD.name: (
                "Sort attributes by the filterable in dashboard flag"
            ),
            AttributeSortField.STOREFRONT_SEARCH_POSITION.name: (
                "Sort attributes by their position in storefront"
            ),
            AttributeSortField.AVAILABLE_IN_GRID.name: (
                "Sort attributes based on whether they can be displayed "
                "or not in a product grid."
            ),
        }
        if self.name in descriptions:
            return descriptions[self.name]
        raise ValueError("Unsupported enum value: %s" % self.value)


class AttributeSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = AttributeSortField
        type_name = "attributes"


class AttributeChoicesSortField(graphene.Enum):
    NAME = ["name", "slug"]
    SLUG = ["slug"]

    @property
    def description(self):
        descriptions = {
            AttributeSortField.NAME.name: "Sort attribute choice by name.",
            AttributeSortField.SLUG.name: "Sort attribute choice by slug.",
        }
        if self.name in descriptions:
            return descriptions[self.name]
        raise ValueError("Unsupported enum value: %s" % self.value)


class AttributeChoicesSortingInput(SortInputObjectType):
    class Meta:
        sort_enum = AttributeChoicesSortField
        type_name = "attribute choices"


def sort_attribute_values(attribute_values, sort_by):
    sort_reverse = False
    direction = sort_by.get("direction", OrderDirection.ASC) if sort_by else None
    if direction == OrderDirection.DESC:
        sort_reverse = True

    sort_field = (
        sort_by.get("field", AttributeChoicesSortField.NAME)
        if sort_by
        else AttributeChoicesSortField.NAME
    )

    if sort_field == AttributeChoicesSortField.SLUG:
        attribute_values = sorted(
            attribute_values, key=lambda val: val.slug, reverse=sort_reverse
        )
    else:
        attribute_values = sorted(
            attribute_values, key=lambda val: (val.slug, val.name), reverse=sort_reverse
        )

    return attribute_values
