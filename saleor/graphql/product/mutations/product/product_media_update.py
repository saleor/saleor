import graphene

from .....permission.enums import ProductPermissions
from .....product import models
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import BaseMutation
from ....core.types import BaseInputObjectType, ProductError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Product, ProductMedia


class ProductMediaUpdateInput(BaseInputObjectType):
    alt = graphene.String(description="Alt text for a product media.")

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


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
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        media = cls.get_node_or_error(info, id, only_type=ProductMedia)
        product = models.Product.objects.prefetched_for_webhook().get(
            pk=media.product_id
        )
        alt = input.get("alt")
        if alt is not None:
            media.alt = alt
            media.save(update_fields=["alt"])
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_updated, product)
        cls.call_event(manager.product_media_updated, media)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductMediaUpdate(product=product, media=media)
