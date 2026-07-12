import graphene
from django.core.exceptions import ValidationError

from .....permission.enums import ProductPermissions
from .....product import models
from .....product.error_codes import VariantMediaReorderErrorCode
from ....core import ResolveInfo
from ....core.context import ChannelContext
from ....core.descriptions import ADDED_IN_324
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import BaseMutation
from ....core.types import NonNullList
from ....core.types.common import VariantMediaReorderError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import ProductMedia, ProductVariant
from ...utils import update_ordered_variant_media

MEDIA_IDS_LIMIT = 100


class VariantMediaReorder(BaseMutation):
    product_variant = graphene.Field(ProductVariant)
    media = NonNullList(ProductMedia)

    class Arguments:
        variant_id = graphene.ID(
            required=True,
            description="ID of a product variant that media order will be altered.",
        )
        media_ids = NonNullList(
            graphene.ID,
            required=True,
            description="IDs of a product variant media in the desired order."
            f" Limited to {MEDIA_IDS_LIMIT} items." + ADDED_IN_324,
        )

    class Meta:
        description = (
            "Changes ordering of the media of a product variant, independently"
            " from the ordering of the parent product's media." + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = VariantMediaReorderError
        error_type_field = "variant_media_reorder_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, media_ids, variant_id
    ):
        variant = cls.get_node_or_error(
            info,
            variant_id,
            field="variant_id",
            only_type=ProductVariant,
            qs=models.ProductVariant.objects.all(),
        )

        if len(media_ids) > MEDIA_IDS_LIMIT:
            raise ValidationError(
                {
                    "media_ids": ValidationError(
                        f"Cannot reorder more than {MEDIA_IDS_LIMIT} media items.",
                        code=VariantMediaReorderErrorCode.INVALID.value,
                    )
                }
            )

        if len(media_ids) != variant.variant_media.count():
            raise ValidationError(
                {
                    "media_ids": ValidationError(
                        "Incorrect number of media IDs provided.",
                        code=VariantMediaReorderErrorCode.INVALID.value,
                    )
                }
            )

        ordered_media = [
            cls.get_node_or_error(
                info, media_id, field="media_ids", only_type=ProductMedia
            )
            for media_id in media_ids
        ]

        update_ordered_variant_media(variant, ordered_media)

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_variant_updated, variant)
        variant = ChannelContext(node=variant, channel_slug=None)
        return VariantMediaReorder(product_variant=variant, media=ordered_media)
