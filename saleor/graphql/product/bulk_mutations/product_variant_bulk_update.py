from collections import defaultdict
from typing import cast

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from graphene.utils.str_converters import to_camel_case

from ....core.tracing import traced_atomic_transaction
from ....permission.enums import ProductPermissions
from ....product import models
from ....product.error_codes import ProductErrorCode
from ....product.search import update_product_search_vector
from ....product.tasks import update_product_discounted_price_task
from ....warehouse import models as warehouse_models
from ...channel import ChannelContext
from ...core.descriptions import ADDED_IN_311, PREVIEW_FEATURE
from ...core.enums import ErrorPolicyEnum
from ...core.mutations import BaseMutation
from ...core.types import NonNullList, ProductVariantBulkError
from ...core.utils import get_duplicated_values
from ...plugins.dataloaders import get_plugin_manager_promise
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

    class Meta:
        description = "Input fields to update product variants." + ADDED_IN_311


class ProductVariantBulkUpdate(BaseMutation):
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
        error_policy = ErrorPolicyEnum(
            required=False,
            default_value=ErrorPolicyEnum.REJECT_EVERYTHING.value,
            description=(
                "Policies of error handling. DEFAULT: "
                + ErrorPolicyEnum.REJECT_EVERYTHING.name
            ),
        )

    class Meta:
        description = (
            "Update multiple product variants." + ADDED_IN_311 + PREVIEW_FEATURE
        )
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductVariantBulkError

    @classmethod
    def save(cls, info, instance, cleaned_input):
        ProductVariantBulkCreate.save(info, instance, cleaned_input)

    @classmethod
    def clean_variants(
        cls,
        info,
        variants,
        product,
        variants_global_id_to_instance_map,
        index_error_map,
    ):
        cleaned_inputs_map = {}
        warehouse_global_id_to_instance_map = {
            graphene.Node.to_global_id("Warehouse", warehouse.id): warehouse
            for warehouse in warehouse_models.Warehouse.objects.all()
        }
        product_channel_global_id_to_instance_map = {
            graphene.Node.to_global_id("Channel", listing.channel_id): listing.channel
            for listing in models.ProductChannelListing.objects.select_related(
                "channel"
            ).filter(product=product.id)
        }
        used_attribute_values = get_used_variants_attribute_values(product)
        variant_attributes_ids = {
            graphene.Node.to_global_id("Attribute", attr_id)
            for attr_id in list(
                product.product_type.variant_attributes.all().values_list(
                    "pk", flat=True
                )
            )
        }
        duplicated_sku = get_duplicated_values(
            [variant.sku for variant in variants if variant.sku]
        )

        for index, variant_data in enumerate(variants):
            variant_id = variant_data["id"]
            variant_data["product_type"] = product.product_type
            variant_data["product"] = product

            if variant_id not in variants_global_id_to_instance_map.keys():
                message = f"Variant #{variant_id} does not exist."
                index_error_map[index].append(
                    ProductVariantBulkError(
                        field="id", message=message, code=ProductErrorCode.INVALID
                    )
                )
                continue

            cleaned_input = ProductVariantBulkCreate.clean_variant(
                info,
                variant_data,
                product_channel_global_id_to_instance_map,
                warehouse_global_id_to_instance_map,
                used_attribute_values,
                variant_attributes_ids,
                duplicated_sku,
                index_error_map,
                index,
                errors=None,
                input_class=ProductVariantBulkUpdateInput,
            )

            cleaned_inputs_map[index] = cleaned_input
        return cleaned_inputs_map

    @classmethod
    def update_variants(cls, info, cleaned_inputs_map, index_error_map):
        instances_data_and_errors_list = []

        for index, cleaned_input in cleaned_inputs_map.items():
            if not cleaned_input:
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )
                continue
            try:
                metadata_list = cleaned_input.pop("metadata", None)
                private_metadata_list = cleaned_input.pop("private_metadata", None)
                instance = cleaned_input.pop("id")
                instance = cls.construct_instance(instance, cleaned_input)
                cls.validate_and_update_metadata(
                    instance, metadata_list, private_metadata_list
                )
                cls.clean_instance(info, instance)
                instances_data_and_errors_list.append(
                    {
                        "instance": instance,
                        "errors": index_error_map[index],
                        "cleaned_input": cleaned_input,
                    }
                )
            except ValidationError as exc:
                for key, value in exc.error_dict.items():
                    for e in value:
                        index_error_map[index].append(
                            ProductVariantBulkError(
                                field=to_camel_case(key),
                                message=e.messages[0],
                                code=e.code,
                            )
                        )
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )
        return instances_data_and_errors_list

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
    def save_variants(cls, info, manager, instances_data_with_errors_list):
        for instance_data in instances_data_with_errors_list:
            instance = instance_data["instance"]
            if instance:
                cleaned_input = instance_data.pop("cleaned_input")
                cls.save(info, instance, cleaned_input)
                cls.update_or_create_variant_stocks(instance, cleaned_input, manager)
                cls.update_or_create_variant_channel_listings(instance, cleaned_input)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        index_error_map: dict = defaultdict(list)
        error_policy = data["error_policy"]

        product = cast(
            models.Product,
            cls.get_node_or_error(info, data["product_id"], only_type="Product"),
        )
        variants_global_id_to_instance_map = {
            graphene.Node.to_global_id("ProductVariant", variant.id): variant
            for variant in product.variants.all()
        }

        cleaned_inputs_map = cls.clean_variants(
            info,
            data["variants"],
            product,
            variants_global_id_to_instance_map,
            index_error_map,
        )

        instances_data_with_errors_list = cls.update_variants(
            info, cleaned_inputs_map, index_error_map
        )

        has_errors = any(
            [True if error else False for error in index_error_map.values()]
        )
        if has_errors:
            if error_policy == ErrorPolicyEnum.REJECT_EVERYTHING.value:
                results = [
                    ProductVariantBulkResult(
                        product_variant=None, errors=data.get("errors")
                    )
                    for data in instances_data_with_errors_list
                ]
                return ProductVariantBulkUpdate(count=0, results=results)

            if error_policy == ErrorPolicyEnum.REJECT_FAILED_ROWS.value:
                for data in instances_data_with_errors_list:
                    if data["errors"] and data["instance"]:
                        data["instance"] = None

        manager = get_plugin_manager_promise(info.context).get()
        cls.save_variants(info, manager, instances_data_with_errors_list)

        instances = [
            ChannelContext(node=instance_data["instance"], channel_slug=None)
            for instance_data in instances_data_with_errors_list
            if instance_data["instance"]
        ]

        # Recalculate the "discounted price" for the parent product
        update_product_discounted_price_task.delay(product.pk)
        update_product_search_vector(product)
        transaction.on_commit(
            lambda: [
                manager.product_variant_updated(instance.node) for instance in instances
            ]
        )

        results = [
            ProductVariantBulkResult(
                product_variant=ChannelContext(
                    node=data.get("instance"), channel_slug=None
                ),
                errors=data.get("errors"),
            )
            if data.get("instance")
            else ProductVariantBulkResult(
                product_variant=None, errors=data.get("errors")
            )
            for data in instances_data_with_errors_list
        ]

        return ProductVariantBulkCreate(count=len(instances), results=results)
