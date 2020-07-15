from collections import defaultdict
from typing import TYPE_CHECKING, DefaultDict, Dict, Iterable, List

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.permissions import ProductPermissions
from ....product.error_codes import ProductErrorCode
from ....product.models import ProductChannelListing
from ...channel.types import Channel
from ...core.mutations import BaseMutation
from ...core.types.common import ProductChannelListingError
from ...core.utils import get_duplicated_values, get_duplicates_ids
from ...utils import resolve_global_ids_to_primary_keys
from ..types.products import Product

if TYPE_CHECKING:
    from ....product.models import Product as ProductModel
    from ....channel.models import Channel as ChannelModel

ErrorType = DefaultDict[str, List[ValidationError]]


class ProductChannelListingAddInput(graphene.InputObjectType):
    channel_id = graphene.ID(
        required=True, description="ID of a channel witch be assigned to product."
    )
    is_published = graphene.Boolean(
        description="Determines if product is visible to customers.", required=True
    )
    publication_date = graphene.types.datetime.Date(
        description="Publication date. ISO 8601 standard."
    )


class ProductChannelListingUpdateInput(graphene.InputObjectType):
    add_channels = graphene.List(
        graphene.NonNull(ProductChannelListingAddInput),
        description="List of channel assigned to product.",
        required=False,
    )
    remove_channels = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of channel unassigned from product.",
        required=False,
    )


class ProductChannelListingUpdate(BaseMutation):
    product = graphene.Field(Product, description="An updated product instance.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a product to update.")
        input = ProductChannelListingUpdateInput(
            required=True,
            description="Fields required to create product channel listings.",
        )

    class Meta:
        description = "Update product chanel listing."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductChannelListingError
        error_type_field = "products_errors"

    @classmethod
    def validate_duplicated_ids(
        cls,
        add_channels_ids: Iterable[str],
        remove_channels_ids: Iterable[str],
        errors: ErrorType,
    ):
        duplicated_ids = get_duplicates_ids(add_channels_ids, remove_channels_ids)
        if duplicated_ids:
            error_msg = (
                "The same object cannot be in both lists "
                "for adding and removing items."
            )
            errors["input"].append(
                ValidationError(
                    error_msg,
                    code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
                    params={"channels": list(duplicated_ids)},
                )
            )

    @classmethod
    def validate_duplicated_values(
        cls, channels_ids: Iterable[str], field_name: str, errors: ErrorType
    ):
        duplicates = get_duplicated_values(channels_ids)
        if duplicates:
            errors[field_name].append(
                ValidationError(
                    "Duplicated channel ID.",
                    code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
                    params={"channels": duplicates},
                )
            )

    @classmethod
    def clean_channels(cls, info, input, errors: ErrorType) -> Dict:
        add_channels = input.get("add_channels", [])
        add_channels_ids = [channel["channel_id"] for channel in add_channels]
        remove_channels_ids = input.get("remove_channels", [])

        cls.validate_duplicated_ids(add_channels_ids, remove_channels_ids, errors)
        cls.validate_duplicated_values(add_channels_ids, "add_channels", errors)
        cls.validate_duplicated_values(remove_channels_ids, "remove_channels", errors)

        if errors:
            return {}
        channels_to_add: List["ChannelModel"] = []
        if add_channels_ids:
            channels_to_add = cls.get_nodes_or_error(
                add_channels_ids, "channel_id", Channel
            )
        _, remove_channels_pks = resolve_global_ids_to_primary_keys(
            remove_channels_ids, Channel
        )

        cleaned_input = {"add_channels": [], "remove_channels": remove_channels_pks}

        for channel_listing, channel in zip(add_channels, channels_to_add):
            channel_listing["channel"] = channel
            cleaned_input["add_channels"].append(channel_listing)

        return cleaned_input

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

        cleaned_input = cls.clean_channels(info, input, errors)
        if not product.category:
            cls.validate_product_without_category(cleaned_input, errors)
        if errors:
            raise ValidationError(errors)

        cls.save(info, product, cleaned_input)

        return ProductChannelListingUpdate(product=product)
