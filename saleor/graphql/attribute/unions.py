import graphene

from ...page import models as page_models
from ...product import models as product_models
from ..core.context import ChannelContext
from ..page.types import Page
from ..product.types import Product, ProductVariant


class AttributeValueReferencedObject(graphene.Union):
    class Meta:
        types = (
            Product,
            ProductVariant,
            Page,
        )

    @classmethod
    def resolve_type(cls, instance, info):
        if isinstance(instance, ChannelContext):
            instance = instance.node
        if isinstance(instance, product_models.Product):
            return Product
        if isinstance(instance, product_models.ProductVariant):
            return ProductVariant
        if isinstance(instance, page_models.Page):
            return Page
        return super().resolve_type(instance, info)
