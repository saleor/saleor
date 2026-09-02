import graphene
from django.core.exceptions import ValidationError

from .....permission.enums import ProductPermissions
from .....product import MEDIA_TAG_CHAR_LIMIT, MEDIA_TAGS_LIMIT, models
from .....product.error_codes import ProductErrorCode
from ....core import ResolveInfo
from ....core.context import ChannelContext
from ....core.descriptions import ADDED_IN_323
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import BaseMutation
from ....core.types import BaseInputObjectType, NonNullList, ProductError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Product, ProductMedia
from ...utils import ALT_CHAR_LIMIT, clean_media_tags


class ProductMediaUpdateInput(BaseInputObjectType):
    alt = graphene.String(description="Alt text for a product media.")
    tags = NonNullList(
        graphene.String,
        required=False,
        description=(
            f"List of tags to assign to the media. Replaces all existing tags; "
            f"pass an empty list to clear them, or omit the field to leave them "
            f"unchanged. Tags are stripped, lowercased and deduplicated. Maximum "
            f"of {MEDIA_TAGS_LIMIT} tags, {MEDIA_TAG_CHAR_LIMIT} characters each."
            + ADDED_IN_323
        ),
    )

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
        product = models.Product.objects.get(pk=media.product_id)
        update_fields = []
        alt = input.get("alt")
        if alt is not None:
            if len(alt) > ALT_CHAR_LIMIT:
                raise ValidationError(
                    {
                        "input": ValidationError(
                            f"Alt field exceeds the character "
                            f"limit of {ALT_CHAR_LIMIT}.",
                            code=ProductErrorCode.INVALID.value,
                        )
                    }
                )
            media.alt = alt
            update_fields.append("alt")
        tags = input.get("tags")
        if tags is not None:
            media.tags = clean_media_tags(tags, ProductErrorCode)
            update_fields.append("tags")
        if update_fields:
            media.save(update_fields=update_fields)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_updated, product)
        cls.call_event(manager.product_media_updated, media)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductMediaUpdate(product=product, media=media)
