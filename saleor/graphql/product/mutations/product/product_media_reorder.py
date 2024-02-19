import graphene
from django.core.exceptions import ValidationError

from .....permission.enums import ProductPermissions
from .....product import models
from .....product.error_codes import ProductErrorCode
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import BaseMutation
from ....core.types import NonNullList, ProductError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Product, ProductMedia
from ...utils import update_ordered_media


class ProductMediaReorder(BaseMutation):
    product = graphene.Field(Product)
    media = NonNullList(ProductMedia)

    class Arguments:
        product_id = graphene.ID(
            required=True,
            description="ID of product that media order will be altered.",
        )
        media_ids = NonNullList(
            graphene.ID,
            required=True,
            description="IDs of a product media in the desired order.",
        )

    class Meta:
        description = "Changes ordering of the product media."
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, media_ids, product_id
    ):
        product = cls.get_node_or_error(
            info,
            product_id,
            field="product_id",
            only_type=Product,
            qs=models.Product.objects.all(),
        )

        if len(media_ids) != product.media.count():
            raise ValidationError(
                {
                    "order": ValidationError(
                        "Incorrect number of media IDs provided.",
                        code=ProductErrorCode.INVALID.value,
                    )
                }
            )

        ordered_media = []
        for media_id in media_ids:
            media = cls.get_node_or_error(
                info, media_id, field="order", only_type=ProductMedia
            )
            if media and media.product != product:
                raise ValidationError(
                    {
                        "order": ValidationError(
                            "Media %(media_id)s does not belong to this product.",
                            code=ProductErrorCode.NOT_PRODUCTS_IMAGE.value,
                            params={"media_id": media_id},
                        )
                    }
                )
            ordered_media.append(media)

        update_ordered_media(ordered_media)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_updated, product)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductMediaReorder(product=product, media=ordered_media)
