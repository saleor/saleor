import graphene

from ...product import ProductMediaTypes, ProductTypeKind
from ..core.enums import to_enum

ProductTypeKindEnum = to_enum(ProductTypeKind)
ProductMediaType = to_enum(ProductMediaTypes, type_name="ProductMediaType")


class ProductAttributeType(graphene.Enum):
    PRODUCT = "PRODUCT"
    VARIANT = "VARIANT"


class StockAvailability(graphene.Enum):
    IN_STOCK = "AVAILABLE"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class CollectionPublished(graphene.Enum):
    PUBLISHED = "published"
    HIDDEN = "hidden"


class ProductTypeConfigurable(graphene.Enum):
    CONFIGURABLE = "configurable"
    SIMPLE = "simple"


class ProductTypeEnum(graphene.Enum):
    DIGITAL = "digital"
    SHIPPABLE = "shippable"


class VariantAttributeScope(graphene.Enum):
    ALL = "all"
    VARIANT_SELECTION = "variant_selection"
    NOT_VARIANT_SELECTION = "not_variant_selection"
