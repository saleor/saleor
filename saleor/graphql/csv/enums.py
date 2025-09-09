import graphene

from ...csv import ExportEvents, FileTypes
from ..core.doc_category import DOC_CATEGORY_PRODUCTS
from ..core.enums import to_enum
from ..directives import doc

ExportEventEnum = to_enum(ExportEvents)
FileTypeEnum = to_enum(FileTypes)


@doc(category=DOC_CATEGORY_PRODUCTS)
class ExportScope(graphene.Enum):
    ALL = "all"
    IDS = "ids"
    FILTER = "filter"

    @property
    def description(self):
        # pylint: disable=no-member
        description_mapping = {
            ExportScope.ALL.name: "Export all products.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            ExportScope.IDS.name: "Export products with given ids.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
            ExportScope.FILTER.name: "Export the filtered products.",  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
        }
        if self.name in description_mapping:
            return description_mapping[self.name]
        raise ValueError(f"Unsupported enum value: {self.value}")


@doc(category=DOC_CATEGORY_PRODUCTS)
class ProductFieldEnum(graphene.Enum):
    NAME = "name"
    DESCRIPTION = "description"
    PRODUCT_TYPE = "product type"
    CATEGORY = "category"
    PRODUCT_WEIGHT = "product weight"
    COLLECTIONS = "collections"
    CHARGE_TAXES = "charge taxes"  # deprecated; remove in Saleor 4.0
    PRODUCT_MEDIA = "product media"
    VARIANT_ID = "variant id"
    VARIANT_SKU = "variant sku"
    VARIANT_WEIGHT = "variant weight"
    VARIANT_MEDIA = "variant media"
