import datetime
from collections import defaultdict
from typing import TYPE_CHECKING

import graphene
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError

from ....core.tracing import traced_atomic_transaction
from ....core.utils.date_time import convert_to_utc_date_time
from ....permission.enums import ProductPermissions
from ....product.error_codes import CollectionErrorCode, ProductErrorCode
from ....product.models import (
    CollectionChannelListing,
    ProductChannelListing,
    ProductVariantChannelListing,
)
from ....product.models import Product as ProductModel
from ....product.models import ProductVariant as ProductVariantModel
from ....product.utils.product import mark_products_in_channels_as_dirty
from ...channel import ChannelContext
from ...channel.mutations import BaseChannelListingMutation
from ...channel.types import Channel
from ...core import ResolveInfo
from ...core.descriptions import DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.mutations import BaseMutation
from ...core.scalars import Date, DateTime, PositiveDecimal
from ...core.types import (
    BaseInputObjectType,
    CollectionChannelListingError,
    NonNullList,
    ProductChannelListingError,
)
from ...core.utils import get_duplicated_values
from ...core.validators import (
    validate_one_of_args_is_in_mutation,
    validate_price_precision,
)
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils.validators import check_for_duplicates
from ..types.collections import Collection
from ..types.products import Product, ProductVariant

if TYPE_CHECKING:
    from ....channel.models import Channel as ChannelModel
    from ....product.models import Collection as CollectionModel

ErrorType = defaultdict[str, list[ValidationError]]


class PublishableChannelListingInput(BaseInputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    is_published = graphene.Boolean(
        description="Determines if object is visible to customers."
    )
    publication_date = Date(
        description=(
            f"Publication date. ISO 8601 standard. {DEPRECATED_IN_3X_INPUT} "
            "Use `publishedAt` field instead."
        )
    )
    published_at = DateTime(description="Publication date time. ISO 8601 standard.")

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductChannelListingAddInput(PublishableChannelListingInput):
    visible_in_listings = graphene.Boolean(
        description=(
            "Determines if product is visible in product listings "
            "(doesn't apply to product collections)."
        )
    )
    is_available_for_purchase = graphene.Boolean(
        description=(
            "Determines if product should be available for purchase in this channel. "
            "This does not guarantee the availability of stock. When set to `False`, "
            "this product is still visible to customers, but it cannot be purchased."
        ),
    )
    available_for_purchase_date = Date(
        description=(
            "A start date from which a product will be available for purchase. "
            "When not set and isAvailable is set to True, "
            f"the current day is assumed. {DEPRECATED_IN_3X_INPUT} "
            "Use `availableForPurchaseAt` field instead."
        )
    )
    available_for_purchase_at = DateTime(
        description=(
            "A start date time from which a product will be available "
            "for purchase. When not set and `isAvailable` is set to True, "
            "the current day is assumed."
        )
    )
    add_variants = NonNullList(
        graphene.ID,
        description="List of variants to which the channel should be assigned.",
        required=False,
    )
    remove_variants = NonNullList(
        graphene.ID,
        description="List of variants from which the channel should be unassigned.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductChannelListingUpdateInput(BaseInputObjectType):
    update_channels = NonNullList(
        ProductChannelListingAddInput,
        description=(
            "List of channels to which the product should be assigned or updated."
        ),
        required=False,
    )
    remove_channels = NonNullList(
        graphene.ID,
        description="List of channels from which the product should be unassigned.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


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
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductChannelListingError
        error_type_field = "product_channel_listing_errors"

    @classmethod
    def clean_available_for_purchase(cls, cleaned_input, errors: ErrorType):
        channels_with_invalid_available_for_purchase: list[str] = []
        channels_with_invalid_date: list[str] = []
        for update_channel in cleaned_input.get("update_channels", []):
            is_available_for_purchase = update_channel.get("is_available_for_purchase")
            available_for_purchase_date = update_channel.get(
                "available_for_purchase_date"
            ) or update_channel.get("available_for_purchase_at")
            if not is_available_for_purchase and available_for_purchase_date:
                channels_with_invalid_available_for_purchase.append(
                    update_channel["channel_id"]
                )
            channels_with_invalid_date = cls.clean_available_fo_purchase_date(
                update_channel, channels_with_invalid_date
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
        if channels_with_invalid_date:
            error_msg = (
                "Only one of argument: availableForPurchaseDate or "
                "availableForPurchaseAt must be specified."
            )
            errors["available_for_purchase_date"].append(
                ValidationError(
                    error_msg,
                    code=ProductErrorCode.INVALID.value,
                    params={"channels": channels_with_invalid_date},
                )
            )

    @staticmethod
    def clean_available_fo_purchase_date(
        update_channel_input, channels_with_invalid_date
    ):
        # DEPRECATED
        available_for_purchase_date = update_channel_input.get(
            "available_for_purchase_date"
        )
        available_for_purchase_at = update_channel_input.get(
            "available_for_purchase_at"
        )
        if available_for_purchase_date and available_for_purchase_at:
            channels_with_invalid_date.append(update_channel_input["channel_id"])
        return channels_with_invalid_date

    @classmethod
    def validate_product_without_category(cls, cleaned_input, errors: ErrorType):
        channels_with_published_product_without_category = []
        for update_channel in cleaned_input.get("update_channels", []):
            is_published = update_channel.get("is_published") is True
            is_available_for_purchase = (
                update_channel.get("is_available_for_purchase") is True
            )
            if is_published or is_available_for_purchase:
                channels_with_published_product_without_category.append(
                    update_channel["channel_id"]
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
    def update_channels(cls, product: "ProductModel", update_channels: list[dict]):
        for update_channel in update_channels:
            channel = update_channel["channel"]
            add_variants = update_channel.get("add_variants", None)
            remove_variants = update_channel.get("remove_variants", None)
            defaults = {"currency": channel.currency_code}
            for field in ["is_published", "published_at", "visible_in_listings"]:
                if field in update_channel.keys():
                    defaults[field] = update_channel[field]
            is_available_for_purchase = update_channel.get("is_available_for_purchase")
            if is_available_for_purchase is not None:
                defaults["available_for_purchase_at"] = (
                    cls.get_available_for_purchase_date(
                        is_available_for_purchase, update_channel
                    )
                )
            product_channel_listing, _ = ProductChannelListing.objects.update_or_create(
                product=product, channel=channel, defaults=defaults
            )
            cls.add_variants(channel, add_variants)
            cls.remove_variants(
                product_channel_listing, product, channel, remove_variants
            )

    @staticmethod
    def get_available_for_purchase_date(is_available_for_purchase, update_channel):
        available_for_purchase_date = update_channel.get("available_for_purchase_date")
        available_for_purchase_date = (
            convert_to_utc_date_time(available_for_purchase_date)
            if available_for_purchase_date
            else update_channel.get("available_for_purchase_at")
        )
        if is_available_for_purchase is False:
            return None
        if is_available_for_purchase is True and not available_for_purchase_date:
            return datetime.datetime.now(tz=datetime.UTC)
        return available_for_purchase_date

    @classmethod
    def validate_variants(cls, input, errors):
        for update_channel in input.get("update_channels", []):
            error = check_for_duplicates(
                update_channel, "add_variants", "remove_variants", "variants"
            )
            if error:
                error.code = ProductErrorCode.DUPLICATED_INPUT_ITEM.value
                errors["addVariants"].append(error)

    @classmethod
    def add_variants(cls, channel, add_variants: list[dict]):
        if not add_variants:
            return
        variants = cls.get_nodes_or_error(add_variants, "id", ProductVariant)
        variant_channel_listings = []
        for variant in variants:
            variant_channel_listings.append(
                ProductVariantChannelListing(channel=channel, variant=variant)
            )

        try:
            ProductVariantChannelListing.objects.bulk_create(variant_channel_listings)
        except IntegrityError as e:
            raise ValidationError(
                {
                    "addVariants": ValidationError(
                        "One of channel listing already "
                        "exists for this product variant.",
                        code=ProductErrorCode.ALREADY_EXISTS.value,
                    )
                }
            ) from e

    @classmethod
    def remove_variants(
        cls,
        product_channel_listing,
        product,
        channel,
        remove_variants: list[dict],
    ):
        if not remove_variants:
            return
        variants = cls.get_nodes_or_error(remove_variants, "id", ProductVariant)
        ProductVariantChannelListing.objects.filter(
            channel=channel, variant__in=variants
        ).delete()
        if not ProductVariantChannelListing.objects.filter(
            channel=channel, variant__product_id=product
        ).exists():
            product_channel_listing.delete()

    @classmethod
    def remove_channels(cls, product: "ProductModel", remove_channels: list[dict]):
        ProductChannelListing.objects.filter(
            product=product, channel_id__in=remove_channels
        ).delete()
        ProductVariantChannelListing.objects.filter(
            variant__product_id=product.pk, channel_id__in=remove_channels
        ).delete()

    @classmethod
    def save(cls, info: ResolveInfo, product: "ProductModel", cleaned_input: dict):
        with traced_atomic_transaction():
            cls.update_channels(product, cleaned_input.get("update_channels", []))
            cls.remove_channels(product, cleaned_input.get("remove_channels", []))

    @classmethod
    def post_save_actions(
        cls, info: ResolveInfo, product: "ProductModel", cleaned_input: dict
    ):
        modified_channel_ids = [
            update_channel["channel"].id
            for update_channel in cleaned_input.get("update_channels", [])
        ]
        modified_channel_ids.extend(cleaned_input.get("remove_channels", []))
        cls.call_event(
            mark_products_in_channels_as_dirty,
            {channel_id: {product.pk} for channel_id in modified_channel_ids},
        )
        product = ProductModel.objects.get(pk=product.pk)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_updated, product)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        product = cls.get_node_or_error(info, id, only_type=Product, field="id")
        errors: defaultdict[str, list[ValidationError]] = defaultdict(list)

        cleaned_input = cls.clean_channels(
            info,
            input,
            errors,
            ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
            input_source="update_channels",
        )
        cls.clean_publication_date(
            errors, ProductErrorCode, cleaned_input, input_source="update_channels"
        )
        cls.clean_available_for_purchase(cleaned_input, errors)
        cls.validate_variants(cleaned_input, errors)
        if not product.category:
            cls.validate_product_without_category(cleaned_input, errors)
        if errors:
            raise ValidationError(errors)

        cls.save(info, product, cleaned_input)
        cls.post_save_actions(info, product, cleaned_input)
        return ProductChannelListingUpdate(
            product=ChannelContext(node=product, channel_slug=None)
        )


class ProductVariantChannelListingAddInput(BaseInputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    price = PositiveDecimal(
        required=True, description="Price of the particular variant in channel."
    )
    cost_price = PositiveDecimal(description="Cost price of the variant in channel.")
    preorder_threshold = graphene.Int(
        description="The threshold for preorder variant in channel."
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductVariantChannelListingUpdate(BaseMutation):
    variant = graphene.Field(
        ProductVariant, description="An updated product variant instance."
    )

    class Arguments:
        id = graphene.ID(
            required=False, description="ID of a product variant to update."
        )
        sku = graphene.String(
            required=False, description="SKU of a product variant to update."
        )
        input = NonNullList(
            ProductVariantChannelListingAddInput,
            required=True,
            description=(
                "List of fields required to create or upgrade product variant "
                "channel listings."
            ),
        )

    class Meta:
        description = "Manage product variant prices in channels."
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductChannelListingError
        error_type_field = "product_channel_listing_errors"

    @classmethod
    def clean_channels(cls, info: ResolveInfo, input, errors: ErrorType) -> list:
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
            channels: list[ChannelModel] = []
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
        cls, variant: "ProductVariantModel", cleaned_input: list, errors: ErrorType
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
    def clean_prices(cls, info: ResolveInfo, cleaned_input, errors: ErrorType) -> list:
        for channel_listing_data in cleaned_input:
            price = channel_listing_data.get("price")
            cost_price = channel_listing_data.get("cost_price")
            channel_id = channel_listing_data["channel_id"]
            currency_code = channel_listing_data["channel"].currency_code

            cls.clean_price(price, "price", currency_code, channel_id, errors)
            cls.clean_price(cost_price, "cost_price", currency_code, channel_id, errors)

        return cleaned_input

    @classmethod
    def save(
        cls, info: ResolveInfo, variant: "ProductVariantModel", cleaned_input: list
    ):
        with traced_atomic_transaction():
            for channel_listing_data in cleaned_input:
                channel = channel_listing_data["channel"]
                defaults = {"currency": channel.currency_code}
                if "price" in channel_listing_data.keys():
                    defaults["price_amount"] = channel_listing_data.get("price", None)
                    # set the discounted price the same as price for now, the discounted
                    # value will be calculated asynchronously in the celery task
                    defaults["discounted_price_amount"] = defaults["price_amount"]
                if "cost_price" in channel_listing_data.keys():
                    defaults["cost_price_amount"] = channel_listing_data.get(
                        "cost_price", None
                    )
                if "preorder_threshold" in channel_listing_data.keys():
                    defaults["preorder_quantity_threshold"] = channel_listing_data.get(
                        "preorder_threshold", None
                    )
                ProductVariantChannelListing.objects.update_or_create(
                    variant=variant,
                    channel=channel,
                    defaults=defaults,
                )

    @classmethod
    def post_save_actions(
        cls, info, variant: "ProductVariantModel", cleaned_input: list[dict]
    ):
        channel_ids = [
            channel_listing_data["channel"].id for channel_listing_data in cleaned_input
        ]
        cls.call_event(
            mark_products_in_channels_as_dirty,
            {channel_id: {variant.product_id} for channel_id in channel_ids},
        )
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_variant_updated, variant)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id=None, input, sku=None
    ):
        validate_one_of_args_is_in_mutation("sku", sku, "id", id)

        qs = ProductVariantModel.objects.all()
        if id:
            variant = cls.get_node_or_error(
                info, id, only_type=ProductVariant, field="id", qs=qs
            )
        else:
            variant = qs.filter(sku=sku).first()
            if not variant:
                raise ValidationError(
                    {
                        "sku": ValidationError(
                            f"Couldn't resolve to a node: {sku}", code="not_found"
                        )
                    }
                )

        errors: defaultdict[str, list[ValidationError]] = defaultdict(list)

        cleaned_input = cls.clean_channels(info, input, errors)
        cls.validate_product_assigned_to_channel(variant, cleaned_input, errors)
        cleaned_input = cls.clean_prices(info, cleaned_input, errors)

        if errors:
            raise ValidationError(errors)

        cls.save(info, variant, cleaned_input)
        cls.post_save_actions(info, variant, cleaned_input)
        return ProductVariantChannelListingUpdate(
            variant=ChannelContext(node=variant, channel_slug=None)
        )


class CollectionChannelListingUpdateInput(BaseInputObjectType):
    add_channels = NonNullList(
        PublishableChannelListingInput,
        description="List of channels to which the collection should be assigned.",
        required=False,
    )
    remove_channels = NonNullList(
        graphene.ID,
        description="List of channels from which the collection should be unassigned.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


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
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionChannelListingError
        error_type_field = "collection_channel_listing_errors"

    @classmethod
    def add_channels(cls, collection: "CollectionModel", add_channels: list[dict]):
        for add_channel in add_channels:
            defaults = {}
            for field in ["is_published", "published_at"]:
                if field in add_channel.keys():
                    defaults[field] = add_channel[field]
            CollectionChannelListing.objects.update_or_create(
                collection=collection, channel=add_channel["channel"], defaults=defaults
            )

    @classmethod
    def remove_channels(cls, collection: "CollectionModel", remove_channels: list[int]):
        CollectionChannelListing.objects.filter(
            collection=collection, channel_id__in=remove_channels
        ).delete()

    @classmethod
    def save(
        cls, info: ResolveInfo, collection: "CollectionModel", cleaned_input: dict
    ):
        with traced_atomic_transaction():
            cls.add_channels(collection, cleaned_input.get("add_channels", []))
            cls.remove_channels(collection, cleaned_input.get("remove_channels", []))

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        collection = cls.get_node_or_error(info, id, only_type=Collection, field="id")
        errors: defaultdict[str, list[ValidationError]] = defaultdict(list)

        cleaned_input = cls.clean_channels(
            info,
            input,
            errors,
            CollectionErrorCode.DUPLICATED_INPUT_ITEM.value,
        )
        cls.clean_publication_date(errors, CollectionErrorCode, cleaned_input)
        if errors:
            raise ValidationError(errors)

        cls.save(info, collection, cleaned_input)
        return CollectionChannelListingUpdate(
            collection=ChannelContext(node=collection, channel_slug=None)
        )
