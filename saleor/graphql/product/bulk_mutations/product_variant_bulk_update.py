from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.permissions import ProductPermissions
from ....core.tracing import traced_atomic_transaction
from ....product import models
from ....product.error_codes import ProductErrorCode
from ....product.tasks import update_product_discounted_price_task
from ....warehouse import models as warehouse_models
from ...channel import ChannelContext
from ...core.enums import ErrorPolicyEnum
from ...core.types import BulkProductError, NonNullList
from ...plugins.dataloaders import load_plugin_manager
from ..utils import get_used_variants_attribute_values
from .product_variant_bulk_create import (
    BulkAttributeValueInput,
    ProductVariantBulkCreate,
    ProductVariantBulkCreateInput,
    ProductVariantBulkResult,
)


class ProductVariantBulkUpdateInput(ProductVariantBulkCreateInput):
    id = graphene.ID(description="ID of the product variant to update.", required=True)
    attributes = NonNullList(
        BulkAttributeValueInput,
        required=False,
        description="List of attributes specific to this variant.",
    )


class ProductVariantBulkUpdate(ProductVariantBulkCreate):
    count = graphene.Int(
        required=True,
        default_value=0,
        description="Returns how many objects were updated.",
    )
    results = NonNullList(
        ProductVariantBulkResult,
        required=True,
        default_value=[],
        description="List of the updated variants.",
    )

    class Arguments:
        error_policy = ErrorPolicyEnum(
            required=False,
            default_value=ErrorPolicyEnum.REJECT_EVERYTHING.name,
            description="Policies of error handling.",
        )
        variants = NonNullList(
            ProductVariantBulkUpdateInput,
            required=True,
            description="Input list of product variants to update.",
        )
        product_id = graphene.ID(
            description="ID of the product to update the variants for.",
            name="product",
            required=True,
        )

    class Meta:
        description = "Update a given product variants."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = BulkProductError
        error_type_field = "bulk_product_errors"

    @classmethod
    def clean_variants(
        cls, info, variants, product, variants_global_id_to_instance_map, errors
    ):
        cleaned_inputs = []
        sku_list = []
        used_attribute_values = get_used_variants_attribute_values(product)
        warehouses = warehouse_models.Warehouse.objects.all()

        for index, variant_data in enumerate(variants):
            variant_id = variant_data["id"]
            if variant_id not in variants_global_id_to_instance_map.keys():
                message = f'Variant #{variant_data["id"]} does not exist.'
                errors["id"].append(
                    ValidationError(
                        message, ProductErrorCode.INVALID, params={"index": index}
                    )
                )
                continue

            if variant_data.attributes:
                try:
                    cls.validate_duplicated_attribute_values(
                        variant_data.attributes, used_attribute_values
                    )
                except ValidationError as exc:
                    errors["attributes"].append(
                        ValidationError(exc.message, exc.code, params={"index": index})
                    )

            variant = variants_global_id_to_instance_map[variant_id]
            cleaned_input = cls.clean_variant_input(
                info, variant, variant_data, warehouses, errors, index
            )
            cleaned_input["instance"] = variant
            cleaned_inputs.append(cleaned_input if cleaned_input else None)

            if cleaned_input["sku"]:
                cls.validate_duplicated_sku(
                    cleaned_input["sku"], index, sku_list, errors
                )
        return cleaned_inputs

    @classmethod
    def update_variants(cls, info, cleaned_inputs, errors):
        instances = []
        for index, cleaned_input in enumerate(cleaned_inputs):
            if not cleaned_input:
                continue

            try:
                metadata_list = cleaned_input.pop("metadata", None)
                private_metadata_list = cleaned_input.pop("private_metadata", None)
                instance = cleaned_input.pop("instance")
                instance = cls.construct_instance(instance, cleaned_input)
                cls.validate_and_update_metadata(
                    instance, metadata_list, private_metadata_list
                )
                cls.clean_instance(info, instance)
                instances.append(instance)
            except ValidationError as exc:
                cls.add_indexes_to_errors(index, exc, errors)
        return instances

    @classmethod
    @traced_atomic_transaction()
    def update_or_create_variant_stocks(cls, variant, cleaned_input, manager):
        stocks = []
        if stocks_data := cleaned_input.get("stocks"):
            for stock_data in stocks_data:
                stock, is_created = warehouse_models.Stock.objects.get_or_create(
                    product_variant=variant, warehouse=stock_data["warehouse"]
                )

                if is_created or (stock.quantity <= 0 and stock_data["quantity"] > 0):
                    transaction.on_commit(
                        lambda: manager.product_variant_back_in_stock(stock)
                    )

                if stock_data["quantity"] <= 0:
                    transaction.on_commit(
                        lambda: manager.product_variant_out_of_stock(stock)
                    )

                stock.quantity = stock_data["quantity"]
                stocks.append(stock)

            warehouse_models.Stock.objects.bulk_update(stocks, ["quantity"])

    @classmethod
    def update_or_create_variant_channel_listings(cls, variant, cleaned_input):
        channel_listings_data = cleaned_input.get("channel_listings")
        if not channel_listings_data:
            return

        for channel_listing_data in channel_listings_data:
            channel = channel_listing_data["channel"]
            price = channel_listing_data["price"]
            cost_price = channel_listing_data.get("cost_price")
            preorder_quantity_threshold = channel_listing_data.get("preorder_threshold")

            defaults = {
                "price_amount": price,
                "currency": channel.currency_code,
            }

            if "preorder_threshold" in channel_listing_data:
                defaults["preorder_quantity_threshold"] = preorder_quantity_threshold

            if "cost_price" in channel_listing_data:
                defaults["cost_price_amount"] = cost_price

            models.ProductVariantChannelListing.objects.update_or_create(
                variant=variant, channel=channel, defaults=defaults
            )

    @classmethod
    @traced_atomic_transaction()
    def save_variants(cls, info, manager, instances, cleaned_inputs):
        assert len(instances) == len(
            cleaned_inputs
        ), "There should be the same number of instances and cleaned inputs."
        for instance, cleaned_input in zip(instances, cleaned_inputs):
            cls.save(info, instance, cleaned_input)
            cls.update_or_create_variant_stocks(instance, cleaned_input, manager)
            cls.update_or_create_variant_channel_listings(instance, cleaned_input)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        errors = defaultdict(list)
        product = cls.get_node_or_error(info, data["product_id"], only_type="Product")
        variants = product.variants.all()
        variants_global_id_to_instance_map = {
            graphene.Node.to_global_id("ProductVariant", variant.id): variant
            for variant in variants
        }

        cleaned_inputs = cls.clean_variants(
            info, data["variants"], product, variants_global_id_to_instance_map, errors
        )
        instances = cls.update_variants(info, cleaned_inputs, errors)

        if errors:
            raise ValidationError(errors)

        manager = load_plugin_manager(info.context)
        cls.save_variants(info, manager, instances, cleaned_inputs)

        # Recalculate the "discounted price" for the parent product
        update_product_discounted_price_task.delay(product.pk)

        variants = [
            ChannelContext(node=instance, channel_slug=None) for instance in instances
        ]

        transaction.on_commit(
            lambda: [
                manager.product_variant_updated(instance) for instance in instances
            ]
        )

        return ProductVariantBulkUpdate(
            count=len(variants),
            results=[
                ProductVariantBulkResult(product_variant=variant)
                for variant in variants
            ],
        )
