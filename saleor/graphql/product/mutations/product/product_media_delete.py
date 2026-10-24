import graphene

from .....permission.enums import ProductPermissions
from .....product import models
from ....core import ResolveInfo
from ....core.context import ChannelContext
from ....core.descriptions import ADDED_IN_323
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import ModelWithExtRefMutation
from ....core.types import ProductError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Product, ProductMedia


class ProductMediaDelete(ModelWithExtRefMutation):
    product = graphene.Field(Product)
    media = graphene.Field(ProductMedia)

    class Arguments:
        id = graphene.ID(required=False, description="ID of a product media to delete.")
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a product media to delete.{ADDED_IN_323}",
        )

    class Meta:
        description = "Deletes a product media."
        doc_category = DOC_CATEGORY_PRODUCTS
        model = models.ProductMedia
        object_type = ProductMedia
        return_field_name = "media"
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, external_reference=None, id=None
    ):
        media_obj = cls.get_instance(info, external_reference=external_reference, id=id)
        product = models.Product.objects.get(pk=media_obj.product_id)
        media_id = media_obj.id
        media_obj.delete()
        media_obj.id = media_id
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_updated, product)
        cls.call_event(manager.product_media_deleted, media_obj)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductMediaDelete(product=product, media=media_obj)
