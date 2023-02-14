from collections import defaultdict
from typing import cast

import graphene
from django.core.exceptions import ValidationError
from django.db.models import F
from graphene.utils.str_converters import to_camel_case

from ....core.tracing import traced_atomic_transaction
from ....permission.enums import ProductPermissions
from ....product import models
from ....product.error_codes import ProductErrorCode, ProductVariantBulkErrorCode
from ....product.search import update_product_search_vector
from ....product.tasks import update_product_discounted_price_task
from ....warehouse import models as warehouse_models
from ...attribute.utils import AttributeAssignmentMixin
from ...core.descriptions import ADDED_IN_311, ADDED_IN_312, PREVIEW_FEATURE
from ...core.enums import ErrorPolicyEnum
from ...core.mutations import BaseMutation, ModelMutation
from ...core.scalars import PositiveDecimal
from ...core.types import NonNullList, ProductVariantBulkError
from ...core.utils import get_duplicated_values
from ...plugins.dataloaders import get_plugin_manager_promise
from ..mutations.channels import ProductVariantChannelListingAddInput
from ..mutations.product.product_create import StockInput, StockUpdateInput
from ..utils import clean_variant_sku, get_used_variants_attribute_values
from .product_variant_bulk_create import (
    BulkAttributeValueInput,
    ProductVariantBulkCreate,
    ProductVariantBulkCreateInput,
    ProductVariantBulkResult,
    clean_price,
    get_results,
)


class ProductVariantStocksUpdateInput(graphene.InputObjectType):
    create = NonNullList(
        StockInput,
        description="List of warehouses to create stocks.",
        required=False,
    )
    update = NonNullList(
        StockUpdateInput,
        description="List of stocks to update.",
        required=False,
    )
    remove = NonNullList(
        graphene.ID,
        description="List of stocks to remove.",
        required=False,
    )


class ChannelListingUpdateInput(graphene.InputObjectType):
    channel_listing = graphene.ID(required=True, description="ID of a channel listing.")
    price = PositiveDecimal(description="Price of the particular variant in channel.")
    cost_price = PositiveDecimal(description="Cost price of the variant in channel.")
    preorder_threshold = graphene.Int(
        description="The threshold for preorder variant in channel."
    )


class ProductVariantChannelListingUpdateInput(graphene.InputObjectType):
    create = NonNullList(
        ProductVariantChannelListingAddInput,
        description="List of channels to create variant channel listings.",
        required=False,
    )
    update = NonNullList(
        ChannelListingUpdateInput,
        description="List of channel listings to update.",
        required=False,
    )
    remove = NonNullList(
        graphene.ID,
        description="List of channel listings to remove.",
        required=False,
    )


class ProductVariantBulkUpdateInput(ProductVariantBulkCreateInput):
    id = graphene.ID(description="ID of the product variant to update.", required=True)
    attributes = NonNullList(
        BulkAttributeValueInput,
        required=False,
        description="List of attributes specific to this variant.",
    )
    stocks = graphene.Field(
        ProductVariantStocksUpdateInput,
        description="Stocks input." + ADDED_IN_312 + PREVIEW_FEATURE,
        required=False,
    )

    channel_listings = graphene.Field(
        ProductVariantChannelListingUpdateInput,
        description="Channel listings input." + ADDED_IN_312 + PREVIEW_FEATURE,
        required=False,
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
    def validate_base_fields(
        cls, cleaned_input, duplicated_sku, index_error_map, index
    ):
        return ProductVariantBulkCreate.validate_base_fields(
            cleaned_input, duplicated_sku, None, index_error_map, index
        )

    @classmethod
    def clean_prices(
        cls,
        price,
        cost_price,
        currency_code,
        channel_id,
        variant_index,
        index_error_map,
    ):
        clean_price(
            price,
            "price",
            currency_code,
            channel_id,
            variant_index,
            None,
            index_error_map,
        )
        clean_price(
            cost_price,
            "cost_price",
            currency_code,
            channel_id,
            variant_index,
            None,
            index_error_map,
        )

    @classmethod
    def clean_channel_listings(
        cls,
        cleaned_input,
        product_channel_global_id_to_instance_map,
        listings_global_id_to_instance_map,
        variant_index,
        index_error_map,
    ):
        wrong_listings_ids: list = []

        if listings_data := cleaned_input["channel_listings"].get("create"):
            cleaned_input["channel_listings"][
                "create"
            ] = ProductVariantBulkCreate.clean_channel_listings(
                listings_data,
                product_channel_global_id_to_instance_map,
                None,
                variant_index,
                index_error_map,
            )
        if listings_data := cleaned_input["channel_listings"].get("update"):
            listings_to_update = []
            for listing_data in listings_data:
                listing_id = listing_data["channel_listing"]

                if listing_id not in listings_global_id_to_instance_map.keys():
                    wrong_listings_ids.append(listing_id)
                    continue

                channel_listing = listings_global_id_to_instance_map[listing_id]
                price = listing_data.get("price")
                cost_price = listing_data.get("cost_price")
                currency_code = channel_listing.currency
                channel_id = channel_listing.channel_id
                errors_count_before_prices = len(index_error_map[variant_index])

                cls.clean_prices(
                    price,
                    cost_price,
                    currency_code,
                    channel_id,
                    variant_index,
                    index_error_map,
                )

                if len(index_error_map[variant_index]) > errors_count_before_prices:
                    continue

                listing_data["channel_listings"] = channel_listing
                listings_to_update.append(listing_data)
            cleaned_input["channel_listings"]["update"] = listings_to_update

        if listings_ids := cleaned_input["channel_listings"].get("remove"):
            listings_to_remove = []
            for listing_id in listings_ids:
                if listing_id not in listings_global_id_to_instance_map.keys():
                    wrong_listings_ids.append(listing_id)
                    continue

                listings_to_remove.append(graphene.Node.from_global_id(listing_id)[1])
            cleaned_input["channel_listings"]["remove"] = listings_to_remove

        if wrong_listings_ids:
            index_error_map[variant_index].append(
                ProductVariantBulkError(
                    field="channelListing",
                    message="Channel listing was not found.",
                    code=ProductVariantBulkErrorCode.NOT_FOUND.value,
                    channel_listings=[wrong_listings_ids],
                )
            )

    @classmethod
    def clean_stocks(
        cls,
        cleaned_input,
        warehouse_global_id_to_instance_map,
        stock_global_id_to_instance_map,
        variant_index,
        index_error_map,
    ):
        wrong_stocks_ids: list = []

        if stocks_data := cleaned_input["stocks"].get("create"):
            cleaned_input["stocks"]["create"] = ProductVariantBulkCreate.clean_stocks(
                stocks_data,
                warehouse_global_id_to_instance_map,
                None,
                variant_index,
                index_error_map,
            )

        if stocks_data := cleaned_input["stocks"].get("update"):
            stocks_to_update = []
            for stock_data in stocks_data:
                stock_id = stock_data["stock"]
                if stock_id not in stock_global_id_to_instance_map.keys():
                    wrong_stocks_ids.append(stock_id)
                    continue

                stock_data["stock"] = stock_global_id_to_instance_map[stock_id]
                stock_data["stock"].quantity = stock_data["quantity"]
                stocks_to_update.append(stock_data)

            cleaned_input["stocks"]["update"] = stocks_to_update

        if stocks_ids := cleaned_input["stocks"].get("remove"):
            stocks_to_remove = []
            for stock_id in stocks_ids:
                if stock_id not in stock_global_id_to_instance_map.keys():
                    wrong_stocks_ids.append(stock_id)
                    continue
                stocks_to_remove.append(graphene.Node.from_global_id(stock_id)[1])
            cleaned_input["stocks"]["remove"] = stocks_to_remove

        if wrong_stocks_ids:
            index_error_map[variant_index].append(
                ProductVariantBulkError(
                    field="stock",
                    message="Stock was not found.",
                    code=ProductVariantBulkErrorCode.NOT_FOUND.value,
                    stocks=[wrong_stocks_ids],
                )
            )

    @classmethod
    def clean_variant(
        cls,
        info,
        variant_data,
        product_channel_global_id_to_instance_map,
        warehouse_global_id_to_instance_map,
        stock_global_id_to_instance_map,
        listings_global_id_to_instance_map,
        variant_attributes,
        used_attribute_values,
        variant_attributes_ids,
        duplicated_sku,
        index_error_map,
        index,
    ):
        cleaned_input = ModelMutation.clean_input(
            info, None, variant_data, input_cls=ProductVariantBulkUpdateInput
        )

        sku = cleaned_input.get("sku")
        if sku is not None:
            cleaned_input["sku"] = clean_variant_sku(sku)

        preorder_settings = cleaned_input.get("preorder")
        if preorder_settings:
            cleaned_input["is_preorder"] = True
            cleaned_input["preorder_global_threshold"] = preorder_settings.get(
                "global_threshold"
            )
            cleaned_input["preorder_end_date"] = preorder_settings.get("end_date")

        base_fields_errors_count = cls.validate_base_fields(
            cleaned_input, duplicated_sku, index_error_map, index
        )

        attributes_errors_count = ProductVariantBulkCreate.clean_attributes(
            cleaned_input,
            variant_data["product_type"],
            variant_attributes,
            variant_attributes_ids,
            used_attribute_values,
            None,
            index,
            index_error_map,
        )

        if cleaned_input.get("channel_listings"):
            cls.clean_channel_listings(
                cleaned_input,
                product_channel_global_id_to_instance_map,
                listings_global_id_to_instance_map,
                index,
                index_error_map,
            )

        if cleaned_input.get("stocks"):
            cls.clean_stocks(
                cleaned_input,
                warehouse_global_id_to_instance_map,
                stock_global_id_to_instance_map,
                index,
                index_error_map,
            )

        if base_fields_errors_count > 0 or attributes_errors_count > 0:
            return None

        return cleaned_input if cleaned_input else None

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
        product_type = product.product_type

        # fetch existing data required to validate inputs
        warehouse_global_id_to_instance_map = {
            graphene.Node.to_global_id("Warehouse", warehouse.id): warehouse
            for warehouse in warehouse_models.Warehouse.objects.all()
        }
        stock_global_id_to_instance_map = {
            graphene.Node.to_global_id("Stock", stock.id): stock
            for stock in warehouse_models.Stock.objects.filter(
                product_variant__in=variants_global_id_to_instance_map.values()
            )
        }
        listings_global_id_to_instance_map = {
            graphene.Node.to_global_id(
                "ProductVariantChannelListing", listing.id
            ): listing
            for listing in models.ProductVariantChannelListing.objects.filter(
                variant__in=variants_global_id_to_instance_map.values()
            )
        }
        product_channel_global_id_to_instance_map = {
            graphene.Node.to_global_id("Channel", listing.channel_id): listing.channel
            for listing in models.ProductChannelListing.objects.select_related(
                "channel"
            ).filter(product=product.id)
        }
        used_attribute_values = get_used_variants_attribute_values(product)
        variant_attributes = product_type.variant_attributes.annotate(
            variant_selection=F("attributevariant__variant_selection")
        )
        variant_attributes_ids = {
            graphene.Node.to_global_id("Attribute", variant_attribute.id)
            for variant_attribute in variant_attributes
        }
        duplicated_sku = get_duplicated_values(
            [variant.sku for variant in variants if variant.sku]
        )

        # clean variants inputs
        for index, variant_data in enumerate(variants):
            variant_id = variant_data["id"]
            variant_data["product_type"] = product_type
            variant_data["product"] = product

            if variant_id not in variants_global_id_to_instance_map.keys():
                message = f"Variant #{variant_id} does not exist."
                index_error_map[index].append(
                    ProductVariantBulkError(
                        field="id", message=message, code=ProductErrorCode.INVALID
                    )
                )
                continue

            cleaned_input = cls.clean_variant(
                info,
                variant_data,
                product_channel_global_id_to_instance_map,
                warehouse_global_id_to_instance_map,
                stock_global_id_to_instance_map,
                listings_global_id_to_instance_map,
                variant_attributes,
                used_attribute_values,
                variant_attributes_ids,
                duplicated_sku,
                index_error_map,
                index,
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
    def prepare_stocks(cls, variant, stocks_input, stocks_to_create, stocks_to_update):
        if stocks_data := stocks_input.get("create"):
            stocks_to_create += [
                warehouse_models.Stock(
                    product_variant=variant,
                    warehouse=stock_data["warehouse"],
                    quantity=stock_data["quantity"],
                )
                for stock_data in stocks_data
            ]
        if stocks_data := stocks_input.get("update"):
            stocks_to_update += [stock_data["stock"] for stock_data in stocks_data]

    @classmethod
    def prepare_channel_listings(
        cls, variant, listings_input, listings_to_create, listings_to_update
    ):
        if listings_data := listings_input.get("create"):
            listings_to_create += [
                models.ProductVariantChannelListing(
                    channel=listing_data["channel"],
                    variant=variant,
                    price_amount=listing_data["price"],
                    cost_price_amount=listing_data.get("cost_price"),
                    currency=listing_data["channel"].currency_code,
                    preorder_quantity_threshold=listing_data.get("preorder_threshold"),
                )
                for listing_data in listings_data
            ]

        if listings_data := listings_input.get("update"):
            for listing_data in listings_data:
                listing = listing_data["channel_listings"]
                if "preorder_threshold" in listing_data:
                    listing.preorder_quantity_threshold = listing_data[
                        "preorder_threshold"
                    ]
                if "price" in listing_data:
                    listing.price_amount = listing_data["price"]
                if "cost_price" in listing_data:
                    listing.cost_price_amount = listing_data["cost_price"]
                listings_to_update.append(listing)

    @classmethod
    @traced_atomic_transaction()
    def save_variants(cls, variants_data_with_errors_list):
        variants_to_update: list = []
        stocks_to_create: list = []
        stocks_to_update: list = []
        stocks_to_remove: list = []
        listings_to_create: list = []
        listings_to_update: list = []
        listings_to_remove: list = []

        # prepare instances
        for variant_data in variants_data_with_errors_list:
            variant = variant_data["instance"]

            if not variant:
                continue

            cleaned_input = variant_data.pop("cleaned_input")
            variants_to_update.append(variant)

            if stocks_input := cleaned_input.get("stocks"):
                cls.prepare_stocks(
                    variant, stocks_input, stocks_to_create, stocks_to_update
                )
                if to_remove := stocks_input.get("remove"):
                    stocks_to_remove += to_remove

            if listings_input := cleaned_input.get("channel_listings"):
                cls.prepare_channel_listings(
                    variant, listings_input, listings_to_create, listings_to_update
                )
                if to_remove := listings_input.get("remove"):
                    listings_to_remove += to_remove

            if attributes := cleaned_input.get("attributes"):
                AttributeAssignmentMixin.save(variant, attributes)

        # perform db queries
        models.ProductVariant.objects.bulk_update(
            variants_to_update,
            [
                "name",
                "sku",
                "track_inventory",
                "weight",
                "quantity_limit_per_customer",
                "metadata",
                "private_metadata",
                "external_reference",
            ],
        )
        warehouse_models.Stock.objects.bulk_create(stocks_to_create)
        warehouse_models.Stock.objects.bulk_update(stocks_to_update, ["quantity"])
        models.ProductVariantChannelListing.objects.bulk_create(listings_to_create)
        models.ProductVariantChannelListing.objects.bulk_update(
            listings_to_update,
            fields=["price_amount", "cost_price_amount", "preorder_quantity_threshold"],
        )
        warehouse_models.Stock.objects.filter(id__in=stocks_to_remove).delete()
        models.ProductVariantChannelListing.objects.filter(
            id__in=listings_to_remove
        ).delete()

    @classmethod
    def post_save_actions(cls, info, instances, product):
        manager = get_plugin_manager_promise(info.context).get()

        # Recalculate the "discounted price" for the parent product
        update_product_discounted_price_task.delay(product.pk)
        update_product_search_vector(product)

        for instance in instances:
            cls.call_event(manager.product_variant_updated, instance.node)

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

        # clean and validate inputs
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

        # check error policy
        if any([True if error else False for error in index_error_map.values()]):
            if error_policy == ErrorPolicyEnum.REJECT_EVERYTHING.value:
                results = get_results(instances_data_with_errors_list, True)
                return ProductVariantBulkUpdate(count=0, results=results)

            if error_policy == ErrorPolicyEnum.REJECT_FAILED_ROWS.value:
                for data in instances_data_with_errors_list:
                    if data["errors"] and data["instance"]:
                        data["instance"] = None

        # save all objects
        cls.save_variants(instances_data_with_errors_list)

        # prepare and return data
        results = get_results(instances_data_with_errors_list)
        instances = [
            result.product_variant for result in results if result.product_variant
        ]
        cls.post_save_actions(info, instances, product)

        return ProductVariantBulkCreate(count=len(instances), results=results)
