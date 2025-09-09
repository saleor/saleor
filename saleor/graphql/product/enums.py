import graphene

from ...product import ProductMediaTypes, ProductTypeKind
from ..core.doc_category import DOC_CATEGORY_PRODUCTS
from ..core.enums import to_enum
from ..directives import doc

ProductTypeKindEnum = doc(DOC_CATEGORY_PRODUCTS, to_enum(ProductTypeKind))

ProductMediaType = doc(
    DOC_CATEGORY_PRODUCTS, to_enum(ProductMediaTypes, type_name="ProductMediaType")
)


@doc(category=DOC_CATEGORY_PRODUCTS)
class ProductAttributeType(graphene.Enum):
    PRODUCT = "PRODUCT"
    VARIANT = "VARIANT"


@doc(category=DOC_CATEGORY_PRODUCTS)
class StockAvailability(graphene.Enum):
    IN_STOCK = "AVAILABLE"
    OUT_OF_STOCK = "OUT_OF_STOCK"


@doc(category=DOC_CATEGORY_PRODUCTS)
class CollectionPublished(graphene.Enum):
    PUBLISHED = "published"
    HIDDEN = "hidden"


@doc(category=DOC_CATEGORY_PRODUCTS)
class ProductTypeConfigurable(graphene.Enum):
    CONFIGURABLE = "configurable"
    SIMPLE = "simple"


@doc(category=DOC_CATEGORY_PRODUCTS)
class ProductTypeEnum(graphene.Enum):
    DIGITAL = "digital"
    SHIPPABLE = "shippable"


@doc(category=DOC_CATEGORY_PRODUCTS)
class VariantAttributeScope(graphene.Enum):
    ALL = "all"
    VARIANT_SELECTION = "variant_selection"
    NOT_VARIANT_SELECTION = "not_variant_selection"
