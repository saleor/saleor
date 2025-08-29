import graphene

from ...page import models as page_models
from ...product import models as product_models
from ..core import ResolveInfo
from ..page.types import PageType
from ..product.types import ProductType


class ReferenceType(graphene.Union):
    class Meta:
        description = (
            "The reference types (product or page type) that are used to narrow down "
            "the choices of reference objects.\n"
            "ProductType applicable for reference attribute with `PRODUCT` or "
            "`PRODUCT_VARIANT` entity type.\n"
            "PageType applicable for reference attribute with `PAGE` entity type."
        )
        types = (ProductType, PageType)

    @classmethod
    def resolve_type(cls, instance, info: ResolveInfo):
        if isinstance(instance, product_models.ProductType):
            return ProductType
        if isinstance(instance, page_models.PageType):
            return PageType

        return super().resolve_type(instance, info)
