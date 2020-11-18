import graphene

from ...csv import ExportEvents, FileTypes
from ...graphql.core.enums import to_enum

ExportEventEnum = to_enum(ExportEvents)
FileTypeEnum = to_enum(FileTypes)


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
    PRODUCT_TYPE = "product type"
    CATEGORY = "category"
    VISIBLE = "visible"
    PRODUCT_WEIGHT = "product weight"
    COLLECTIONS = "collections"
    CHARGE_TAXES = "charge taxes"
    PRODUCT_IMAGES = "product images"
    VARIANT_SKU = "variant sku"
    VARIANT_WEIGHT = "variant weight"
    VARIANT_IMAGES = "variant images"
