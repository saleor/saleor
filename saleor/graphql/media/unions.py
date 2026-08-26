import graphene

from ...page import models as page_models
from ...product import models as product_models
from ..core import ResolveInfo
from ..core.context import ChannelContext
from ..page.types import Page
from ..product.types import Category, Collection, Product

# Kept out of the package `__init__` on purpose: graphene resolves union members
# eagerly, so every member type must already be fully initialized.


class MediaOwner(graphene.Union):
    class Meta:
        description = "The entity a media object belongs to."
        types = (Product, Category, Collection, Page)

    @classmethod
    def resolve_type(cls, instance, info: ResolveInfo):
        node = instance.node if isinstance(instance, ChannelContext) else instance
        if isinstance(node, product_models.Product):
            return Product
        if isinstance(node, product_models.Category):
            return Category
        if isinstance(node, product_models.Collection):
            return Collection
        if isinstance(node, page_models.Page):
            return Page
        return super().resolve_type(instance, info)
