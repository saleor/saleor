from typing import Final

import graphene

from ...product import ProductMediaTypes, ProductTypeKind
from ..core.doc_category import DOC_CATEGORY_PRODUCTS
from ..core.enums import to_enum
from ..core.types import BaseEnum

ProductTypeKindEnum: Final[graphene.Enum] = to_enum(ProductTypeKind)
ProductTypeKindEnum.doc_category = DOC_CATEGORY_PRODUCTS

ProductMediaType: Final[graphene.Enum] = to_enum(
    ProductMediaTypes, type_name="ProductMediaType"
)
ProductMediaType.doc_category = DOC_CATEGORY_PRODUCTS


class ProductAttributeType(BaseEnum):
    PRODUCT = "PRODUCT"
    VARIANT = "VARIANT"

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class StockAvailability(BaseEnum):
    IN_STOCK = "AVAILABLE"
    OUT_OF_STOCK = "OUT_OF_STOCK"

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class CollectionPublished(BaseEnum):
    PUBLISHED = "published"
    HIDDEN = "hidden"

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductTypeConfigurable(BaseEnum):
    CONFIGURABLE = "configurable"
    SIMPLE = "simple"

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductTypeEnum(BaseEnum):
    DIGITAL = "digital"
    SHIPPABLE = "shippable"

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS

    @property
    def deprecation_reason(self):
        deprecations = {
            ProductTypeEnum.DIGITAL.name: (  # type: ignore[attr-defined] # graphene.Enum is not typed # noqa: E501
                "DIGITAL will removed in Saleor 3.24.0, use metadata or "
                "attributes instead."
            )
        }
        if self.name in deprecations:
            return deprecations[self.name]
        return None


class VariantAttributeScope(BaseEnum):
    ALL = "all"
    VARIANT_SELECTION = "variant_selection"
    NOT_VARIANT_SELECTION = "not_variant_selection"

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS
