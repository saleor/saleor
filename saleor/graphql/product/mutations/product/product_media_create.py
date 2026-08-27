from typing import Any

import graphene
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .....permission.enums import ProductPermissions
from .....product import ProductMediaTypes, models
from .....product.error_codes import ProductErrorCode
from .....product.tasks import fetch_product_media_image_task
from ....core import ResolveInfo
from ....core.context import ChannelContext
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import BaseMutation
from ....core.types import BaseInputObjectType, ProductError, Upload
from ....core.validators.file import clean_image_file
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Product, ProductMedia
from ...utils import probe_media_url, validate_media_input


class ProductMediaCreateInput(BaseInputObjectType):
    alt = graphene.String(description="Alt text for a product media.")
    image = Upload(
        required=False, description="Represents an image file in a multipart request."
    )
    product = graphene.ID(
        required=True, description="ID of an product.", name="product"
    )
    media_url = graphene.String(
        required=False, description="Represents an URL to an external media."
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductMediaCreate(BaseMutation):
    product = graphene.Field(Product)
    media = graphene.Field(ProductMedia)

    class Arguments:
        input = ProductMediaCreateInput(
            required=True, description="Fields required to create a product media."
        )

    class Meta:
        description = (
            "Create a media object (image or video URL) associated with product. "
            "For image, this mutation must be sent as a `multipart` request. "
            "More detailed specs of the upload format can be found here: "
            "https://github.com/jaydenseric/graphql-multipart-request-spec"
        )
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def validate_input(cls, input):
        if not input.get("product"):
            raise ValidationError(
                {
                    "product": ValidationError(
                        "Product ID is required.",
                        code=ProductErrorCode.REQUIRED.value,
                    )
                }
            )

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        cls.validate_input(input)

        image = input.get("image")
        media_url = input.get("media_url")
        alt = input.get("alt") or ""

        if error := validate_media_input(image, media_url, alt, ProductErrorCode):
            error_message, error_code, _ = error
            raise ValidationError(
                {
                    "input": ValidationError(
                        error_message,
                        code=error_code,
                    )
                }
            )

        product = cls.get_node_or_error(
            info,
            input["product"],
            field="product",
            only_type=Product,
            qs=models.Product.objects.all(),
        )

        media_data: dict[str, Any] | None = None
        fetch_image = False
        if image:
            input["image"] = info.context.FILES.get(image)
            image_data = clean_image_file(input, "image", ProductErrorCode)
            media_data = {
                "image": image_data,
                "alt": alt,
                "type": ProductMediaTypes.IMAGE,
            }
        elif media_url:
            # Remote URLs can point to the images or oembed data.
            # In case of images, the image is fetched asynchronously by a task.
            # Otherwise we keep only URL to remote media.
            probe_result = probe_media_url(media_url, ProductErrorCode)
            if probe_result.is_image:
                media_data = {
                    "external_url": media_url,
                    "alt": alt,
                    "type": ProductMediaTypes.IMAGE,
                }
                fetch_image = True
            else:
                oembed_data = probe_result.oembed_data
                media_data = {
                    "external_url": oembed_data["url"],
                    "alt": oembed_data.get("title", alt),
                    "type": probe_result.media_type,
                    "oembed_data": oembed_data,
                }

        media = None
        if media_data:
            # The product can be deleted concurrently while the image is uploaded or
            # the remote URL is probed, so the insert may fail on the foreign key.
            try:
                with transaction.atomic():
                    media = product.media.create(**media_data)
            except IntegrityError as e:
                if not models.Product.objects.filter(pk=product.pk).exists():
                    raise ValidationError(
                        {
                            "product": ValidationError(
                                "Product no longer exists.",
                                code=ProductErrorCode.NOT_FOUND.value,
                            )
                        }
                    ) from e
                # Any other constraint violation is a bug, not a lost race.
                raise
            if fetch_image:
                fetch_product_media_image_task.delay(media.pk)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_updated, product)
        cls.call_event(manager.product_media_created, media)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductMediaCreate(product=product, media=media)
