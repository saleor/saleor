from collections import defaultdict
from typing import TYPE_CHECKING, DefaultDict, Dict, List

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.permissions import ProductPermissions
from ....product.error_codes import ProductErrorCode
from ....product.models import ProductChannelListing
from ...channel import ChannelContext
from ...channel.mutations import BaseChannelListing
from ...core.types.common import ProductChannelListingError
from ..types.products import Product

if TYPE_CHECKING:
    from ....product.models import Product as ProductModel

ErrorType = DefaultDict[str, List[ValidationError]]


class ProductChannelListingAddInput(graphene.InputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    is_published = graphene.Boolean(
        description="Determines if product is visible to customers.", required=True
    )
    publication_date = graphene.types.datetime.Date(
        description="Publication date. ISO 8601 standard."
    )


class ProductChannelListingUpdateInput(graphene.InputObjectType):
    add_channels = graphene.List(
        graphene.NonNull(ProductChannelListingAddInput),
        description="List of channels to which the product should be assigned.",
        required=False,
    )
    remove_channels = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of channels from which the product should be unassigned.",
        required=False,
    )


class ProductChannelListingUpdate(BaseChannelListing):
    product = graphene.Field(Product, description="An updated product instance.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a product to update.")
        input = ProductChannelListingUpdateInput(
            required=True,
            description="Fields required to create product channel listings.",
        )

    class Meta:
        description = "Manage product's availability in channels."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductChannelListingError
        error_type_field = "products_errors"

    @classmethod
    def validate_product_without_category(cls, cleaned_input, errors: ErrorType):
        channels_with_published_product_without_category = []
        for add_channel in cleaned_input.get("add_channels", []):
            if add_channel.get("is_published") is True:
                channels_with_published_product_without_category.append(
                    add_channel["channel_id"]
                )
        if channels_with_published_product_without_category:
            errors["is_published"].append(
                ValidationError(
                    "You must select a category to be able to publish.",
                    code=ProductErrorCode.PRODUCT_WITHOUT_CATEGORY.value,
                    params={
                        "channels": channels_with_published_product_without_category
                    },
                )
            )

    @classmethod
    def add_channels(cls, product: "ProductModel", add_channels: List[Dict]):
        for add_channel in add_channels:
            defaults = {
                "is_published": add_channel.get("is_published"),
                "publication_date": add_channel.get("publication_date", None),
            }
            ProductChannelListing.objects.update_or_create(
                product=product, channel=add_channel["channel"], defaults=defaults
            )

    @classmethod
    def remove_channels(cls, product: "ProductModel", remove_channels: List[int]):
        ProductChannelListing.objects.filter(
            product=product, channel_id__in=remove_channels
        ).delete()

    @classmethod
    @transaction.atomic()
    def save(cls, info, product: "ProductModel", cleaned_input: Dict):
        cls.add_channels(product, cleaned_input.get("add_channels", []))
        cls.remove_channels(product, cleaned_input.get("remove_channels", []))

    @classmethod
    def perform_mutation(cls, _root, info, id, input):
        product = cls.get_node_or_error(info, id, only_type=Product, field="id")
        errors = defaultdict(list)

        cleaned_input = cls.clean_channels(
            info, input, errors, ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
        )
        if not product.category:
            cls.validate_product_without_category(cleaned_input, errors)
        if errors:
            raise ValidationError(errors)

        cls.save(info, product, cleaned_input)
        return ProductChannelListingUpdate(
            product=ChannelContext(node=product, channel_slug=None)
        )
