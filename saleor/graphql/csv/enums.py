import graphene

from ...csv import ExportEvents
from ...graphql.core.enums import to_enum

ExportEventEnum = to_enum(ExportEvents)


class ExportScope(graphene.Enum):
    ALL = "all"
    IDS = "ids"
    FILTER = "filter"

    @property
    def description(self):
        # pylint: disable=no-member
        description_mapping = {
            ExportScope.ALL.name: "Export all products.",
            ExportScope.IDS.name: "Export products with given ids.",
            ExportScope.FILTER.name: "Export the filtered products.",
        }
        if self.name in description_mapping:
            return description_mapping[self.name]
        raise ValueError("Unsupported enum value: %s" % self.value)


class ProductFieldEnum(graphene.Enum):
    NAME = "name"
    DESCRIPTION = "description"
    PRODUCT_TYPE = "product_type"
    CATEGORY = "category"
    VISIBLE = "visible"
    COLLECTIONS = "collections"
    PRICE = "price"
    PRICE_OVERRIDE = "price_override"
    IMAGES = "images"
    WEIGHT = "weight"
    CHARGE_TAXES = "charge_taxes"
