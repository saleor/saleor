import graphene

from .....core.permissions import ProductPermissions
from .....product import models
from ....channel import ChannelContext
from ....core.mutations import BaseMutation
from ....core.types import ProductError
from ....plugins.dataloaders import load_plugin_manager
from ...types import Product, ProductMedia


class ProductMediaUpdateInput(graphene.InputObjectType):
    alt = graphene.String(description="Alt text for a product media.")


class ProductMediaUpdate(BaseMutation):
    product = graphene.Field(Product)
    media = graphene.Field(ProductMedia)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a product media to update.")
        input = ProductMediaUpdateInput(
            required=True, description="Fields required to update a product media."
        )

    class Meta:
        description = "Updates a product media."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        media = cls.get_node_or_error(info, data.get("id"), only_type=ProductMedia)
        product = models.Product.objects.prefetched_for_webhook().get(
            pk=media.product_id
        )
        alt = data.get("input").get("alt")
        if alt is not None:
            media.alt = alt
            media.save(update_fields=["alt"])
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.product_updated, product)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductMediaUpdate(product=product, media=media)
