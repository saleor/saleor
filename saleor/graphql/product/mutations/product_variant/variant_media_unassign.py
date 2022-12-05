import graphene
from django.core.exceptions import ValidationError

from .....core.permissions import ProductPermissions
from .....product import models
from .....product.error_codes import ProductErrorCode
from ....channel import ChannelContext
from ....core.mutations import BaseMutation
from ....core.types import ProductError
from ....plugins.dataloaders import load_plugin_manager
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
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, media_id, variant_id):
        media = cls.get_node_or_error(
            info, media_id, field="image_id", only_type=ProductMedia
        )
        qs = models.ProductVariant.objects.prefetched_for_webhook()
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
                        code=ProductErrorCode.NOT_PRODUCTS_IMAGE,
                    )
                }
            )
        else:
            variant_media.delete()

        variant = ChannelContext(node=variant, channel_slug=None)
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.product_variant_updated, variant.node)
        return VariantMediaUnassign(product_variant=variant, media=media)
