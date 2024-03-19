import graphene
from django.core.exceptions import ValidationError

from .....permission.enums import ProductPermissions
from .....product import models
from .....product.error_codes import ProductErrorCode
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import BaseMutation
from ....core.types import ProductError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import ProductMedia, ProductVariant


class VariantMediaUnassign(BaseMutation):
    product_variant = graphene.Field(ProductVariant)
    media = graphene.Field(ProductMedia)

    class Arguments:
        media_id = graphene.ID(
            required=True,
            description="ID of a product media to unassign from a variant.",
        )
        variant_id = graphene.ID(required=True, description="ID of a product variant.")

    class Meta:
        description = "Unassign an media from a product variant."
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, media_id, variant_id
    ):
        media = cls.get_node_or_error(
            info, media_id, field="image_id", only_type=ProductMedia
        )
        qs = models.ProductVariant.objects.all()
        variant = cls.get_node_or_error(
            info, variant_id, field="variant_id", only_type=ProductVariant, qs=qs
        )

        try:
            variant_media = models.VariantMedia.objects.get(
                media=media, variant=variant
            )
        except models.VariantMedia.DoesNotExist:
            raise ValidationError(
                {
                    "media_id": ValidationError(
                        "Media is not assigned to this variant.",
                        code=ProductErrorCode.NOT_PRODUCTS_IMAGE.value,
                    )
                }
            )
        else:
            variant_media.delete()

        variant = ChannelContext(node=variant, channel_slug=None)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_variant_updated, variant.node)
        return VariantMediaUnassign(product_variant=variant, media=media)
