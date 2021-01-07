import datetime
from collections import defaultdict
from typing import TYPE_CHECKING, DefaultDict, Dict, List

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.permissions import ProductPermissions
from ....product.error_codes import CollectionErrorCode, ProductErrorCode
from ....product.models import (
    CollectionChannelListing,
    ProductChannelListing,
    ProductVariantChannelListing,
)
from ....product.tasks import update_product_discounted_price_task
from ...channel import ChannelContext
from ...channel.mutations import BaseChannelListingMutation
from ...channel.types import Channel
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.types.common import (
    CollectionChannelListingError,
    ProductChannelListingError,
)
from ...core.utils import get_duplicated_values
from ...core.validators import validate_price_precision
from ..types.products import Collection, Product, ProductVariant

if TYPE_CHECKING:
    from ....channel.models import Channel as ChannelModel
    from ....product.models import Collection as CollectionModel
    from ....product.models import Product as ProductModel
    from ....product.models import ProductVariant as ProductVariantModel

ErrorType = DefaultDict[str, List[ValidationError]]


class PublishableChannelListingInput(graphene.InputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    is_published = graphene.Boolean(
        description="Determines if object is visible to customers."
    )
    publication_date = graphene.types.datetime.Date(
        description="Publication date. ISO 8601 standard."
    )


class ProductChannelListingAddInput(PublishableChannelListingInput):
    visible_in_listings = graphene.Boolean(
        description=(
            "Determines if product is visible in product listings "
            "(doesn't apply to product collections)."
        )
    )
    is_available_for_purchase = graphene.Boolean(
        description="Determine if product should be available for purchase.",
    )
    available_for_purchase_date = graphene.Date(
        description=(
            "A start date from which a product will be available for purchase. "
            "When not set and isAvailable is set to True, "
            "the current day is assumed."
        )
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


class ProductChannelListingUpdate(BaseChannelListingMutation):
    product = graphene.Field(Product, description="An updated product instance.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a product to update.")
        input = ProductChannelListingUpdateInput(
            required=True,
            description="Fields required to create or update product channel listings.",
        )

    class Meta:
        description = "Manage product's availability in channels."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductChannelListingError
        error_type_field = "product_channel_listing_errors"

    @classmethod
    def clean_available_for_purchase(cls, cleaned_input, errors: ErrorType):
        channels_with_invalid_available_for_purchase = []
        for add_channel in cleaned_input.get("add_channels", []):
            is_available_for_purchase = add_channel.get("is_available_for_purchase")
            available_for_purchase_date = add_channel.get("available_for_purchase_date")
            if not is_available_for_purchase and available_for_purchase_date:
                channels_with_invalid_available_for_purchase.append(
                    add_channel["channel_id"]
                )
        if channels_with_invalid_available_for_purchase:
            error_msg = (
                "Cannot set available for purchase date when"
                " isAvailableForPurchase is false."
            )
            errors["available_for_purchase_date"].append(
                ValidationError(
                    error_msg,
                    code=ProductErrorCode.INVALID.value,
                    params={"channels": channels_with_invalid_available_for_purchase},
                )
            )

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
            channel = add_channel["channel"]
            defaults = {"currency": channel.currency_code}
            for field in ["is_published", "publication_date", "visible_in_listings"]:
                if field in add_channel.keys():
                    defaults[field] = add_channel.get(field, None)
            is_available_for_purchase = add_channel.get("is_available_for_purchase")
            available_for_purchase_date = add_channel.get("available_for_purchase_date")
            if is_available_for_purchase is not None:
                if is_available_for_purchase is False:
                    defaults["available_for_purchase"] = None
                elif (
                    is_available_for_purchase is True
                    and not available_for_purchase_date
                ):
                    defaults["available_for_purchase"] = datetime.date.today()
                else:
                    defaults["available_for_purchase"] = available_for_purchase_date
            ProductChannelListing.objects.update_or_create(
                product=product, channel=channel, defaults=defaults
            )

    @classmethod
    def remove_channels(cls, product: "ProductModel", remove_channels: List[int]):
        ProductChannelListing.objects.filter(
            product=product, channel_id__in=remove_channels
        ).delete()
        ProductVariantChannelListing.objects.filter(
            variant__product_id=product.pk, channel_id__in=remove_channels
        ).delete()

    @classmethod
    @transaction.atomic()
    def save(cls, info, product: "ProductModel", cleaned_input: Dict):
        cls.add_channels(product, cleaned_input.get("add_channels", []))
        cls.remove_channels(product, cleaned_input.get("remove_channels", []))
        info.context.plugins.product_updated(product)

    @classmethod
    def perform_mutation(cls, _root, info, id, input):
        product = cls.get_node_or_error(info, id, only_type=Product, field="id")
        errors = defaultdict(list)

        cleaned_input = cls.clean_channels(
            info,
            input,
            errors,
            ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
        )
        cls.clean_publication_date(cleaned_input)
        cls.clean_available_for_purchase(cleaned_input, errors)
        if not product.category:
            cls.validate_product_without_category(cleaned_input, errors)
        if errors:
            raise ValidationError(errors)

        cls.save(info, product, cleaned_input)
        return ProductChannelListingUpdate(
            product=ChannelContext(node=product, channel_slug=None)
        )


class ProductVariantChannelListingAddInput(graphene.InputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    price = PositiveDecimal(
        required=True, description="Price of the particular variant in channel."
    )
    cost_price = PositiveDecimal(description="Cost price of the variant in channel.")


class ProductVariantChannelListingUpdate(BaseMutation):
    variant = graphene.Field(
        ProductVariant, description="An updated product variant instance."
    )

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of a product variant to update."
        )
        input = graphene.List(
            graphene.NonNull(ProductVariantChannelListingAddInput),
            required=True,
            description=(
                "List of fields required to create or upgrade product variant ",
                "channel listings.",
            ),
        )

    class Meta:
        description = "Manage product variant prices in channels."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductChannelListingError
        error_type_field = "product_channel_listing_errors"

    @classmethod
    def clean_channels(cls, info, input, errors: ErrorType) -> List:
        add_channels_ids = [
            channel_listing_data["channel_id"] for channel_listing_data in input
        ]
        cleaned_input = []

        duplicates = get_duplicated_values(add_channels_ids)
        if duplicates:
            errors["channelId"].append(
                ValidationError(
                    "Duplicated channel ID.",
                    code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
                    params={"channels": duplicates},
                )
            )
        else:
            channels: List["ChannelModel"] = []
            if add_channels_ids:
                channels = cls.get_nodes_or_error(
                    add_channels_ids, "channel_id", Channel
                )
            for channel_listing_data, channel in zip(input, channels):
                channel_listing_data["channel"] = channel
                cleaned_input.append(channel_listing_data)
        return cleaned_input

    @classmethod
    def validate_product_assigned_to_channel(
        cls, variant: "ProductVariantModel", cleaned_input: List, errors: ErrorType
    ):
        channel_pks = [
            channel_listing_data["channel"].pk for channel_listing_data in cleaned_input
        ]
        channels_assigned_to_product = list(
            ProductChannelListing.objects.filter(
                product=variant.product_id
            ).values_list("channel_id", flat=True)
        )
        channels_not_assigned_to_product = set(channel_pks) - set(
            channels_assigned_to_product
        )
        if channels_not_assigned_to_product:
            channel_global_ids = []
            for channel_listing_data in cleaned_input:
                if (
                    channel_listing_data["channel"].pk
                    in channels_not_assigned_to_product
                ):
                    channel_global_ids.append(channel_listing_data["channel_id"])
            errors["input"].append(
                ValidationError(
                    "Product not available in channels.",
                    code=ProductErrorCode.PRODUCT_NOT_ASSIGNED_TO_CHANNEL.value,
                    params={"channels": channel_global_ids},
                )
            )

    @classmethod
    def clean_price(cls, price, field_name, currency, channel_id, errors: ErrorType):
        try:
            validate_price_precision(price, currency)
        except ValidationError as error:
            error.code = ProductErrorCode.INVALID.value
            error.params = {
                "channels": [channel_id],
            }
            errors[field_name].append(error)

    @classmethod
    def clean_prices(cls, info, cleaned_input, errors: ErrorType) -> List:
        for channel_listing_data in cleaned_input:
            price = channel_listing_data.get("price")
            cost_price = channel_listing_data.get("cost_price")
            channel_id = channel_listing_data["channel_id"]
            currency_code = channel_listing_data["channel"].currency_code

            cls.clean_price(price, "price", currency_code, channel_id, errors)
            cls.clean_price(cost_price, "cost_price", currency_code, channel_id, errors)

        return cleaned_input

    @classmethod
    @transaction.atomic()
    def save(cls, info, variant: "ProductVariantModel", cleaned_input: List):
        for channel_listing_data in cleaned_input:
            channel = channel_listing_data["channel"]
            defaults = {"currency": channel.currency_code}
            if "price" in channel_listing_data.keys():
                defaults["price_amount"] = channel_listing_data.get("price", None)
            if "cost_price" in channel_listing_data.keys():
                defaults["cost_price_amount"] = channel_listing_data.get(
                    "cost_price", None
                )
            ProductVariantChannelListing.objects.update_or_create(
                variant=variant,
                channel=channel,
                defaults=defaults,
            )
        update_product_discounted_price_task.delay(variant.product_id)
        info.context.plugins.product_updated(variant.product)

    @classmethod
    def perform_mutation(cls, _root, info, id, input):
        variant: "ProductVariantModel" = cls.get_node_or_error(  # type: ignore
            info, id, only_type=ProductVariant, field="id"
        )
        errors = defaultdict(list)

        cleaned_input = cls.clean_channels(info, input, errors)
        cls.validate_product_assigned_to_channel(variant, cleaned_input, errors)
        cleaned_input = cls.clean_prices(info, cleaned_input, errors)

        if errors:
            raise ValidationError(errors)

        cls.save(info, variant, cleaned_input)

        return ProductVariantChannelListingUpdate(
            variant=ChannelContext(node=variant, channel_slug=None)
        )


class CollectionChannelListingUpdateInput(graphene.InputObjectType):
    add_channels = graphene.List(
        graphene.NonNull(PublishableChannelListingInput),
        description="List of channels to which the collection should be assigned.",
        required=False,
    )
    remove_channels = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of channels from which the collection should be unassigned.",
        required=False,
    )


class CollectionChannelListingUpdate(BaseChannelListingMutation):
    collection = graphene.Field(
        Collection, description="An updated collection instance."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a collection to update.")
        input = CollectionChannelListingUpdateInput(
            required=True,
            description=(
                "Fields required to create or update collection channel listings."
            ),
        )

    class Meta:
        description = "Manage collection's availability in channels."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionChannelListingError
        error_type_field = "collection_channel_listing_errors"

    @classmethod
    def add_channels(cls, collection: "CollectionModel", add_channels: List[Dict]):
        for add_channel in add_channels:
            defaults = {}
            for field in ["is_published", "publication_date"]:
                if field in add_channel.keys():
                    defaults[field] = add_channel.get(field, None)
            CollectionChannelListing.objects.update_or_create(
                collection=collection, channel=add_channel["channel"], defaults=defaults
            )

    @classmethod
    def remove_channels(cls, collection: "CollectionModel", remove_channels: List[int]):
        CollectionChannelListing.objects.filter(
            collection=collection, channel_id__in=remove_channels
        ).delete()

    @classmethod
    @transaction.atomic()
    def save(cls, info, collection: "CollectionModel", cleaned_input: Dict):
        cls.add_channels(collection, cleaned_input.get("add_channels", []))
        cls.remove_channels(collection, cleaned_input.get("remove_channels", []))

    @classmethod
    def perform_mutation(cls, _root, info, id, input):
        collection = cls.get_node_or_error(info, id, only_type=Collection, field="id")
        errors = defaultdict(list)

        cleaned_input = cls.clean_channels(
            info,
            input,
            errors,
            CollectionErrorCode.DUPLICATED_INPUT_ITEM.value,
        )
        cls.clean_publication_date(cleaned_input)
        if errors:
            raise ValidationError(errors)

        cls.save(info, collection, cleaned_input)
        return CollectionChannelListingUpdate(
            collection=ChannelContext(node=collection, channel_slug=None)
        )
