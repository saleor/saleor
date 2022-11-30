from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from graphene.types import InputObjectType

from ....core.permissions import ProductPermissions
from ....core.tracing import traced_atomic_transaction
from ....product import models
from ....product.error_codes import ProductErrorCode
from ....product.search import update_product_search_vector
from ....product.tasks import update_product_discounted_price_task
from ....product.utils.variants import generate_and_set_variant_name
from ...attribute.utils import AttributeAssignmentMixin
from ...channel import ChannelContext
from ...channel.types import Channel
from ...core.mutations import BaseMutation, ModelMutation
from ...core.types import BulkProductError, NonNullList
from ...core.utils import get_duplicated_values
from ...core.validators import validate_price_precision
from ...plugins.dataloaders import load_plugin_manager
from ...warehouse.types import Warehouse
from ..mutations.channels import ProductVariantChannelListingAddInput
from ..mutations.product.product_create import StockInput
from ..mutations.product_variant.product_variant_create import (
    ProductVariantCreate,
    ProductVariantInput,
)
from ..types import ProductVariant
from ..utils import clean_variant_sku, create_stocks, get_used_variants_attribute_values


class BulkAttributeValueInput(InputObjectType):
    id = graphene.ID(description="ID of the selected attribute.")
    values = NonNullList(
        graphene.String,
        required=False,
        description=(
            "The value or slug of an attribute to resolve. "
            "If the passed value is non-existent, it will be created."
        ),
    )
    boolean = graphene.Boolean(
        required=False,
        description=(
            "The boolean value of an attribute to resolve. "
            "If the passed value is non-existent, it will be created."
        ),
    )


class ProductVariantBulkCreateInput(ProductVariantInput):
    attributes = NonNullList(
        BulkAttributeValueInput,
        required=True,
        description="List of attributes specific to this variant.",
    )
    stocks = NonNullList(
        StockInput,
        description="Stocks of a product available for sale.",
        required=False,
    )
    channel_listings = NonNullList(
        ProductVariantChannelListingAddInput,
        description="List of prices assigned to channels.",
        required=False,
    )
    sku = graphene.String(description="Stock keeping unit.")


class ProductVariantBulkCreate(BaseMutation):
    count = graphene.Int(
        required=True,
        default_value=0,
        description="Returns how many objects were created.",
    )
    product_variants = NonNullList(
        ProductVariant,
        required=True,
        default_value=[],
        description="List of the created variants.",
    )

    class Arguments:
        variants = NonNullList(
            ProductVariantBulkCreateInput,
            required=True,
            description="Input list of product variants to create.",
        )
        product_id = graphene.ID(
            description="ID of the product to create the variants for.",
            name="product",
            required=True,
        )

    class Meta:
        description = "Creates product variants for a given product."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = BulkProductError
        error_type_field = "bulk_product_errors"

    @classmethod
    def clean_variant_input(
        cls,
        info,
        instance: models.ProductVariant,
        data: dict,
        errors: dict,
        variant_index: int,
    ):
        cleaned_input = ModelMutation.clean_input(
            info, instance, data, input_cls=ProductVariantBulkCreateInput
        )

        attributes = cleaned_input.get("attributes")
        if attributes:
            try:
                cleaned_input["attributes"] = ProductVariantCreate.clean_attributes(
                    attributes, data["product_type"]
                )
            except ValidationError as exc:
                exc.params = {"index": variant_index}
                errors["attributes"] = exc

        channel_listings = cleaned_input.get("channel_listings")
        if channel_listings:
            cleaned_input["channel_listings"] = cls.clean_channel_listings(
                channel_listings, errors, data["product"], variant_index
            )

        stocks = cleaned_input.get("stocks")
        if stocks:
            cls.clean_stocks(stocks, errors, variant_index)

        cleaned_input["sku"] = clean_variant_sku(cleaned_input.get("sku"))

        preorder_settings = cleaned_input.get("preorder")
        if preorder_settings:
            cleaned_input["is_preorder"] = True
            cleaned_input["preorder_global_threshold"] = preorder_settings.get(
                "global_threshold"
            )
            cleaned_input["preorder_end_date"] = preorder_settings.get("end_date")

        return cleaned_input

    @classmethod
    def clean_price(
        cls, price, field_name, currency, channel_id, variant_index, errors
    ):
        try:
            validate_price_precision(price, currency)
        except ValidationError as error:
            error.code = ProductErrorCode.INVALID.value
            error.params = {
                "channels": [channel_id],
                "index": variant_index,
            }
            errors[field_name].append(error)

    @classmethod
    def clean_channel_listings(cls, channels_data, errors, product, variant_index):
        channel_ids = [
            channel_listing["channel_id"] for channel_listing in channels_data
        ]
        duplicates = get_duplicated_values(channel_ids)
        if duplicates:
            errors["channel_listings"] = ValidationError(
                "Duplicated channel ID.",
                code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
                params={"channels": duplicates, "index": variant_index},
            )
            return channels_data
        channels = cls.get_nodes_or_error(
            channel_ids, "channel_listings", only_type=Channel
        )
        for index, channel_listing_data in enumerate(channels_data):
            channel_listing_data["channel"] = channels[index]

        for channel_listing_data in channels_data:
            price = channel_listing_data.get("price")
            cost_price = channel_listing_data.get("cost_price")
            channel_id = channel_listing_data["channel_id"]
            currency_code = channel_listing_data["channel"].currency_code
            cls.clean_price(
                price, "price", currency_code, channel_id, variant_index, errors
            )
            cls.clean_price(
                cost_price,
                "cost_price",
                currency_code,
                channel_id,
                variant_index,
                errors,
            )

        channels_not_assigned_to_product = []
        channels_assigned_to_product = list(
            models.ProductChannelListing.objects.filter(product=product.id).values_list(
                "channel_id", flat=True
            )
        )
        for channel_listing_data in channels_data:
            if channel_listing_data["channel"].id not in channels_assigned_to_product:
                channels_not_assigned_to_product.append(
                    channel_listing_data["channel_id"]
                )
        if channels_not_assigned_to_product:
            errors["channel_id"].append(
                ValidationError(
                    "Product not available in channels.",
                    code=ProductErrorCode.PRODUCT_NOT_ASSIGNED_TO_CHANNEL.value,
                    params={
                        "index": variant_index,
                        "channels": channels_not_assigned_to_product,
                    },
                )
            )
        return channels_data

    @classmethod
    def clean_stocks(cls, stocks_data, errors, variant_index):
        warehouse_ids = [stock["warehouse"] for stock in stocks_data]
        duplicates = get_duplicated_values(warehouse_ids)
        if duplicates:
            errors["stocks"] = ValidationError(
                "Duplicated warehouse ID.",
                code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
                params={"warehouses": duplicates, "index": variant_index},
            )

    @classmethod
    def add_indexes_to_errors(cls, index, error, error_dict):
        """Append errors with index in params to mutation error dict."""
        for key, value in error.error_dict.items():
            for e in value:
                if e.params:
                    e.params["index"] = index
                else:
                    e.params = {"index": index}
            error_dict[key].extend(value)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()

        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)
            if not instance.name:
                generate_and_set_variant_name(instance, cleaned_input.get("sku"))

    @classmethod
    def create_variants(cls, info, cleaned_inputs, product, errors):
        instances = []
        for index, cleaned_input in enumerate(cleaned_inputs):
            if not cleaned_input:
                continue
            try:
                instance = models.ProductVariant()
                cleaned_input["product"] = product
                instance = cls.construct_instance(instance, cleaned_input)
                cls.clean_instance(info, instance)
                instances.append(instance)
            except ValidationError as exc:
                cls.add_indexes_to_errors(index, exc, errors)
        return instances

    @classmethod
    def validate_duplicated_sku(cls, sku, index, sku_list, errors):
        if sku in sku_list:
            errors["sku"].append(
                ValidationError(
                    "Duplicated SKU.", ProductErrorCode.UNIQUE, params={"index": index}
                )
            )
        sku_list.append(sku)

    @classmethod
    def validate_duplicated_attribute_values(
        cls, attributes_data, used_attribute_values, instance=None
    ):
        attribute_values = defaultdict(list)
        for attr in attributes_data:
            if "boolean" in attr:
                attribute_values[attr.id] = attr["boolean"]
            else:
                attribute_values[attr.id].extend(attr.get("values", []))
        if attribute_values in used_attribute_values:
            raise ValidationError(
                "Duplicated attribute values for product variant.",
                ProductErrorCode.DUPLICATED_INPUT_ITEM,
            )
        used_attribute_values.append(attribute_values)

    @classmethod
    def clean_variants(cls, info, variants, product, errors):
        cleaned_inputs = []
        sku_list = []
        used_attribute_values = get_used_variants_attribute_values(product)
        for index, variant_data in enumerate(variants):
            if variant_data.attributes:
                try:
                    cls.validate_duplicated_attribute_values(
                        variant_data.attributes, used_attribute_values
                    )
                except ValidationError as exc:
                    errors["attributes"].append(
                        ValidationError(exc.message, exc.code, params={"index": index})
                    )

            variant_data["product_type"] = product.product_type
            variant_data["product"] = product
            cleaned_input = cls.clean_variant_input(
                info, None, variant_data, errors, index
            )

            cleaned_inputs.append(cleaned_input if cleaned_input else None)

            if cleaned_input["sku"]:
                cls.validate_duplicated_sku(
                    cleaned_input["sku"], index, sku_list, errors
                )
        return cleaned_inputs

    @classmethod
    def create_variant_channel_listings(cls, variant, cleaned_input):
        channel_listings_data = cleaned_input.get("channel_listings")
        if not channel_listings_data:
            return
        variant_channel_listings = []
        for channel_listing_data in channel_listings_data:
            channel = channel_listing_data["channel"]
            price = channel_listing_data["price"]
            cost_price = channel_listing_data.get("cost_price")
            preorder_quantity_threshold = channel_listing_data.get("preorder_threshold")
            variant_channel_listings.append(
                models.ProductVariantChannelListing(
                    channel=channel,
                    variant=variant,
                    price_amount=price,
                    cost_price_amount=cost_price,
                    currency=channel.currency_code,
                    preorder_quantity_threshold=preorder_quantity_threshold,
                )
            )
        models.ProductVariantChannelListing.objects.bulk_create(
            variant_channel_listings
        )

    @classmethod
    @traced_atomic_transaction()
    def save_variants(cls, info, instances, product, cleaned_inputs):
        assert len(instances) == len(
            cleaned_inputs
        ), "There should be the same number of instances and cleaned inputs."
        for instance, cleaned_input in zip(instances, cleaned_inputs):
            cls.save(info, instance, cleaned_input)
            cls.create_variant_stocks(instance, cleaned_input)
            cls.create_variant_channel_listings(instance, cleaned_input)

        if not product.default_variant:
            product.default_variant = instances[0]
            product.save(update_fields=["default_variant", "updated_at"])

    @classmethod
    def create_variant_stocks(cls, variant, cleaned_input):
        stocks = cleaned_input.get("stocks")
        if not stocks:
            return
        warehouse_ids = [stock["warehouse"] for stock in stocks]
        warehouses = cls.get_nodes_or_error(
            warehouse_ids, "warehouse", only_type=Warehouse
        )
        create_stocks(variant, stocks, warehouses)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        product = cls.get_node_or_error(info, data["product_id"], only_type="Product")
        errors = defaultdict(list)

        cleaned_inputs = cls.clean_variants(info, data["variants"], product, errors)
        instances = cls.create_variants(info, cleaned_inputs, product, errors)
        if errors:
            raise ValidationError(errors)
        cls.save_variants(info, instances, product, cleaned_inputs)

        # Recalculate the "discounted price" for the parent product
        update_product_discounted_price_task.delay(product.pk)

        instances = [
            ChannelContext(node=instance, channel_slug=None) for instance in instances
        ]

        update_product_search_vector(product)
        manager = load_plugin_manager(info.context)
        transaction.on_commit(
            lambda: [
                manager.product_variant_created(instance.node) for instance in instances
            ]
        )

        return ProductVariantBulkCreate(
            count=len(instances), product_variants=instances
        )
