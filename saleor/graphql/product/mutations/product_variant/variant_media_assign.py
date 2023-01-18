import graphene
from django.core.exceptions import ValidationError

from .....core.tracing import traced_atomic_transaction
from .....permission.enums import ProductPermissions
from .....product import models
from .....product.error_codes import ProductErrorCode
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.mutations import BaseMutation
from ....core.types import ProductError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import ProductMedia, ProductVariant


class VariantMediaAssign(BaseMutation):
    product_variant = graphene.Field(ProductVariant)
    media = graphene.Field(ProductMedia)

    class Arguments:
        media_id = graphene.ID(
            required=True, description="ID of a product media to assign to a variant."
        )
        variant_id = graphene.ID(required=True, description="ID of a product variant.")

    class Meta:
        description = "Assign an media to a product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, media_id, variant_id
    ):
        media = cls.get_node_or_error(
            info, media_id, field="media_id", only_type=ProductMedia
        )
        qs = models.ProductVariant.objects.prefetched_for_webhook()
        variant = cls.get_node_or_error(
            info, variant_id, field="variant_id", only_type=ProductVariant, qs=qs
        )
        with traced_atomic_transaction():
            if media and variant:
                # check if the given image and variant can be matched together
                media_belongs_to_product = variant.product.media.filter(
                    pk=media.pk
                ).first()
                if media_belongs_to_product:
                    _, created = media.variant_media.get_or_create(variant=variant)
                    if not created:
                        raise ValidationError(
                            {
                                "media_id": ValidationError(
                                    "This media is already assigned",
                                    code=ProductErrorCode.MEDIA_ALREADY_ASSIGNED.value,
                                )
                            }
                        )
                else:
                    raise ValidationError(
                        {
                            "media_id": ValidationError(
                                "This media doesn't belong to that product.",
                                code=ProductErrorCode.NOT_PRODUCTS_IMAGE.value,
                            )
                        }
                    )
            variant = ChannelContext(node=variant, channel_slug=None)
            manager = get_plugin_manager_promise(info.context).get()
            cls.call_event(manager.product_variant_updated, variant.node)
        return VariantMediaAssign(product_variant=variant, media=media)
