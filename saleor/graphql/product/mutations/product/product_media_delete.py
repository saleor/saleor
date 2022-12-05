import graphene

from .....core.permissions import ProductPermissions
from .....product import models
from ....channel import ChannelContext
from ....core.mutations import BaseMutation
from ....core.types import ProductError
from ....plugins.dataloaders import load_plugin_manager
from ...types import Product, ProductMedia


class ProductMediaDelete(BaseMutation):
    product = graphene.Field(Product)
    media = graphene.Field(ProductMedia)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a product media to delete.")

    class Meta:
        description = "Deletes a product media."

        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        media_obj = cls.get_node_or_error(info, data.get("id"), only_type=ProductMedia)
        media_id = media_obj.id
        media_obj.delete()
        media_obj.id = media_id
        product = models.Product.objects.prefetched_for_webhook().get(
            pk=media_obj.product_id
        )
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.product_updated, product)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductMediaDelete(product=product, media=media_obj)
