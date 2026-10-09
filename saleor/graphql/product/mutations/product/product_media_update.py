import graphene
from django.core.exceptions import ValidationError

from .....permission.enums import ProductPermissions
from .....product import models
from .....product.error_codes import ProductErrorCode
from ....core import ResolveInfo
from ....core.context import ChannelContext
from ....core.descriptions import ADDED_IN_323
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import ModelWithExtRefMutation
from ....core.types import BaseInputObjectType, ProductError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Product, ProductMedia
from ...utils import ALT_CHAR_LIMIT
from .product_media_create import clean_media_external_reference


class ProductMediaUpdateInput(BaseInputObjectType):
    alt = graphene.String(description="Alt text for a product media.")
    external_reference = graphene.String(
        description=f"External ID of this product media.{ADDED_IN_323}",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductMediaUpdate(ModelWithExtRefMutation):
    product = graphene.Field(Product)
    media = graphene.Field(ProductMedia)

    class Arguments:
        id = graphene.ID(required=False, description="ID of a product media to update.")
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a product media to update.{ADDED_IN_323}",
        )
        input = ProductMediaUpdateInput(
            required=True, description="Fields required to update a product media."
        )

    class Meta:
        description = "Updates a product media."
        doc_category = DOC_CATEGORY_PRODUCTS
        model = models.ProductMedia
        object_type = ProductMedia
        return_field_name = "media"
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input, external_reference=None, id=None
    ):
        media = cls.get_instance(info, external_reference=external_reference, id=id)
        product = models.Product.objects.get(pk=media.product_id)
        update_fields = []
        if "external_reference" in input:
            new_external_reference = input["external_reference"]
            clean_media_external_reference(new_external_reference, media.pk)
            media.external_reference = new_external_reference
            update_fields.append("external_reference")
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
        if update_fields:
            media.save(update_fields=update_fields)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_updated, product)
        cls.call_event(manager.product_media_updated, media)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductMediaUpdate(product=product, media=media)
