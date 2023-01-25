from collections import defaultdict
from typing import cast

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from graphene.types import InputObjectType
from graphene.utils.str_converters import to_camel_case

from ....core.tracing import traced_atomic_transaction
from ....permission.enums import ProductPermissions
from ....product import models
from ....product.error_codes import ProductVariantBulkErrorCode
from ....product.search import update_product_search_vector
from ....product.tasks import update_product_discounted_price_task
from ....product.utils.variants import generate_and_set_variant_name
from ....warehouse import models as warehouse_models
from ...attribute.utils import AttributeAssignmentMixin
from ...channel import ChannelContext
from ...core.descriptions import ADDED_IN_311, DEPRECATED_IN_3X_FIELD, PREVIEW_FEATURE
from ...core.enums import ErrorPolicyEnum
from ...core.mutations import (
    BaseMutation,
    ModelMutation,
    validation_error_to_error_type,
)
from ...core.types import BulkProductError, NonNullList, ProductVariantBulkError
from ...core.utils import get_duplicated_values
from ...core.validators import validate_price_precision
from ...plugins.dataloaders import get_plugin_manager_promise
from ..mutations.channels import ProductVariantChannelListingAddInput
from ..mutations.product.product_create import StockInput
from ..mutations.product_variant.product_variant_create import (
    ProductVariantCreate,
    ProductVariantInput,
)
from ..types import ProductVariant
from ..utils import clean_variant_sku, get_used_variants_attribute_values


class ProductVariantBulkResult(graphene.ObjectType):
    product_variant = graphene.Field(
        ProductVariant, required=False, description="Product variant data."
    )
    errors = NonNullList(
        ProductVariantBulkError,
        required=False,
        description="List of errors occurred on create attempt.",
    )


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
        description="List of the created variants." + DEPRECATED_IN_3X_FIELD,
    )

    results = NonNullList(
        ProductVariantBulkResult,
        required=True,
        default_value=[],
        description="List of the created variants." + ADDED_IN_311,
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
        error_policy = ErrorPolicyEnum(
            required=False,
            default_value=ErrorPolicyEnum.REJECT_EVERYTHING.value,
            description=(
                "Policies of error handling. DEFAULT: "
                + ErrorPolicyEnum.REJECT_EVERYTHING.name
                + ADDED_IN_311
                + PREVIEW_FEATURE
            ),
        )

    class Meta:
        description = "Creates product variants for a given product."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = BulkProductError
        error_type_field = "bulk_product_errors"

    @classmethod
    def clean_attributes(
        cls,
        cleaned_input,
        product_type,
        variant_attributes_ids,
        used_attribute_values,
        errors,
        variant_index,
        index_error_map,
    ):

        attributes_errors_count = 0
        if attributes := cleaned_input.get("attributes"):
            attributes_ids = {attr["id"] for attr in attributes or []}
            invalid_attributes = attributes_ids - variant_attributes_ids
            if len(invalid_attributes) > 0:
                message = "Given attributes are not a variant attributes."
                code = ProductVariantBulkErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.value
                index_error_map[variant_index].append(
                    ProductVariantBulkError(
                        field="attributes", message=message, code=code
                    )
                )
                if errors is not None:
                    errors["attributes"].append(
                        ValidationError(
                            message,
                            code=code,
                            params={
                                "attributes": invalid_attributes,
                                "index": variant_index,
                            },
                        )
                    )
                attributes_errors_count += 1

            if product_type.has_variants:
                try:
                    cleaned_attributes = ProductVariantCreate.clean_attributes(
                        attributes, product_type
                    )
                    ProductVariantCreate.validate_duplicated_attribute_values(
                        cleaned_attributes, used_attribute_values, None
                    )
                    cleaned_input["attributes"] = cleaned_attributes
                except ValidationError as exc:
                    index_error_map[variant_index].append(
                        ProductVariantBulkError(
                            field="attributes", message=exc.message, code=exc.code
                        )
                    )
                    if errors is not None:
                        exc.params = {"index": variant_index}
                        errors["attributes"].append(exc)
                    attributes_errors_count += 1
            else:
                message = "Cannot assign attributes for product type without variants"
                index_error_map[variant_index].append(
                    ProductVariantBulkError(
                        field="attributes",
                        message=message,
                        code=ProductVariantBulkErrorCode.INVALID.value,
                    )
                )
                if errors is not None:
                    errors["attributes"].append(
                        ValidationError(
                            message,
                            code=ProductVariantBulkErrorCode.INVALID.value,
                            params={
                                "attributes": invalid_attributes,
                                "index": variant_index,
                            },
                        )
                    )
                attributes_errors_count += 1
        return attributes_errors_count

    @classmethod
    def clean_price(
        cls,
        price,
        field_name,
        currency,
        channel_id,
        variant_index,
        errors,
        index_error_map,
    ):
        try:
            validate_price_precision(price, currency)
        except ValidationError as error:
            index_error_map[variant_index].append(
                ProductVariantBulkError(
                    field=to_camel_case(field_name),
                    message=error.message,
                    code=ProductVariantBulkErrorCode.INVALID_PRICE.value,
                    channels=[channel_id],
                )
            )
            if errors is not None:
                error.code = ProductVariantBulkErrorCode.INVALID_PRICE.value
                error.params = {
                    "channels": [channel_id],
                    "index": variant_index,
                }
                errors[field_name].append(error)

    @classmethod
    def clean_channel_listings(
        cls,
        cleaned_input,
        product_channel_global_id_to_instance_map,
        errors,
        variant_index,
        index_error_map,
    ):
        channel_listings = cleaned_input.get("channel_listings")
        channel_ids = [
            channel_listing["channel_id"] for channel_listing in channel_listings
        ]
        listings_to_create = []

        duplicates = get_duplicated_values(channel_ids)
        if duplicates:
            message = "Duplicated channel ID."
            index_error_map[variant_index].append(
                ProductVariantBulkError(
                    field="channelListings",
                    message=message,
                    code=ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.value,
                    channels=duplicates,
                )
            )
            if errors is not None:
                errors["channel_listings"] = ValidationError(
                    message=message,
                    code=ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.value,
                    params={"channels": duplicates, "index": variant_index},
                )

        channels_not_assigned_to_product = [
            channel_id
            for channel_id in channel_ids
            if channel_id not in product_channel_global_id_to_instance_map.keys()
        ]

        if channels_not_assigned_to_product:
            message = "Product not available in channels."
            code = ProductVariantBulkErrorCode.PRODUCT_NOT_ASSIGNED_TO_CHANNEL.value
            index_error_map[variant_index].append(
                ProductVariantBulkError(
                    field="channelId",
                    message=message,
                    code=code,
                    channels=channels_not_assigned_to_product,
                )
            )
            if errors is not None:
                errors["channel_id"].append(
                    ValidationError(
                        message=message,
                        code=code,
                        params={
                            "index": variant_index,
                            "channels": channels_not_assigned_to_product,
                        },
                    )
                )

        for channel_listing in channel_listings:
            channel_id = channel_listing["channel_id"]

            if (
                channel_id in channels_not_assigned_to_product
                or channel_id in duplicates
            ):
                continue

            channel_listing["channel"] = product_channel_global_id_to_instance_map[
                channel_id
            ]
            price = channel_listing.get("price")
            cost_price = channel_listing.get("cost_price")
            currency_code = channel_listing["channel"].currency_code

            errors_count_before_prices = len(index_error_map[variant_index])
            cls.clean_price(
                price,
                "price",
                currency_code,
                channel_id,
                variant_index,
                errors,
                index_error_map,
            )
            cls.clean_price(
                cost_price,
                "cost_price",
                currency_code,
                channel_id,
                variant_index,
                errors,
                index_error_map,
            )

            if len(index_error_map[variant_index]) > errors_count_before_prices:
                continue

            listings_to_create.append(channel_listing)

        cleaned_input["channel_listings"] = listings_to_create

    @classmethod
    def clean_stocks(
        cls,
        cleaned_input,
        warehouse_global_id_to_instance_map,
        errors,
        variant_index,
        index_error_map,
    ):
        stocks = cleaned_input.get("stocks")
        stocks_to_create = []
        warehouse_ids = [stock["warehouse"] for stock in stocks]

        wrong_warehouse_ids = {
            warehouse_id
            for warehouse_id in warehouse_ids
            if warehouse_id not in warehouse_global_id_to_instance_map.keys()
        }

        if wrong_warehouse_ids:
            message = "Not existing warehouse ID."
            index_error_map[variant_index].append(
                ProductVariantBulkError(
                    field="warehouses",
                    message=message,
                    code=ProductVariantBulkErrorCode.NOT_FOUND.value,
                    warehouses=wrong_warehouse_ids,
                )
            )
            if errors is not None:
                errors["warehouses"] = ValidationError(
                    message,
                    code=ProductVariantBulkErrorCode.NOT_FOUND.value,
                    params={"warehouses": wrong_warehouse_ids, "index": variant_index},
                )

        duplicates = get_duplicated_values(warehouse_ids)
        if duplicates:
            message = "Duplicated warehouse ID."
            index_error_map[variant_index].append(
                ProductVariantBulkError(
                    field="stocks",
                    message=message,
                    code=ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.value,
                    warehouses=duplicates,
                )
            )
            if errors is not None:
                errors["stocks"] = ValidationError(
                    message,
                    code=ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.value,
                    params={"warehouses": duplicates, "index": variant_index},
                )

        for stock_data in stocks:
            if (
                stock_data["warehouse"] in duplicates
                or stock_data["warehouse"] in wrong_warehouse_ids
            ):
                continue
            else:
                stock_data["warehouse"] = warehouse_global_id_to_instance_map[
                    stock_data["warehouse"]
                ]
                stocks_to_create.append(stock_data)

        cleaned_input["stocks"] = stocks_to_create

    @classmethod
    def add_indexes_to_errors(cls, index, error, error_dict, index_error_map):
        """Append errors with index in params to mutation error dict."""
        for key, value in error.error_dict.items():
            for e in value:
                if e.params:
                    e.params["index"] = index
                else:
                    e.params = {"index": index}
                index_error_map[index].append(
                    ProductVariantBulkError(
                        field=to_camel_case(key),
                        message=e.messages[0],
                        code=e.code,
                    )
                )
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
    def create_variants(
        cls, info, cleaned_inputs_map, product, errors, index_error_map
    ):
        instances_data_and_errors_list = []

        for index, cleaned_input in cleaned_inputs_map.items():
            if not cleaned_input:
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )
                continue
            try:
                instance = models.ProductVariant()
                cleaned_input["product"] = product
                instance = cls.construct_instance(instance, cleaned_input)
                cls.clean_instance(info, instance)
                instances_data_and_errors_list.append(
                    {
                        "instance": instance,
                        "errors": index_error_map[index],
                        "cleaned_input": cleaned_input,
                    }
                )
            except ValidationError as exc:
                cls.add_indexes_to_errors(index, exc, errors, index_error_map)
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )
        return instances_data_and_errors_list

    @classmethod
    def validate_base_fields(
        cls, cleaned_input, duplicated_sku, errors, index_error_map, index
    ):
        base_fields_errors_count = 0
        weight = cleaned_input.get("weight")
        if weight and weight.value < 0:
            message = "Product variant can't have negative weight."
            code = ProductVariantBulkErrorCode.INVALID.value
            index_error_map[index].append(
                ProductVariantBulkError(
                    field="weight",
                    message=message,
                    code=code,
                )
            )
            if errors is not None:
                errors["weight"].append(
                    ValidationError(message, code, params={"index": index})
                )
            base_fields_errors_count += 1

        quantity_limit = cleaned_input.get("quantity_limit_per_customer")
        if quantity_limit is not None and quantity_limit < 1:
            message = (
                "Product variant can't have "
                "quantity_limit_per_customer lower than 1."
            )
            code = ProductVariantBulkErrorCode.INVALID.value
            index_error_map[index].append(
                ProductVariantBulkError(
                    field="quantity_limit_per_customer",
                    message=message,
                    code=code,
                )
            )
            if errors is not None:
                errors["quantity_limit_per_customer"].append(
                    ValidationError(message, code, params={"index": index})
                )
            base_fields_errors_count += 1

        sku = cleaned_input.get("sku")
        if sku is not None and sku in duplicated_sku:
            message = "Duplicated SKU."
            code = ProductVariantBulkErrorCode.UNIQUE.value
            index_error_map[index].append(
                ProductVariantBulkError(field="sku", message=message, code=code)
            )
            if errors is not None:
                errors["sku"].append(
                    ValidationError(message, code, params={"index": index})
                )
            base_fields_errors_count += 1

        return base_fields_errors_count

    @classmethod
    def clean_variant(
        cls,
        info,
        variant_data,
        product_channel_global_id_to_instance_map,
        warehouse_global_id_to_instance_map,
        used_attribute_values,
        variant_attributes_ids,
        duplicated_sku,
        index_error_map,
        index,
        errors,
        input_class=ProductVariantBulkCreateInput,
    ):
        cleaned_input = ModelMutation.clean_input(
            info, None, variant_data, input_cls=input_class
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
            cleaned_input, duplicated_sku, errors, index_error_map, index
        )

        attributes_errors_count = cls.clean_attributes(
            cleaned_input,
            variant_data["product_type"],
            variant_attributes_ids,
            used_attribute_values,
            errors,
            index,
            index_error_map,
        )

        if cleaned_input.get("channel_listings"):
            cls.clean_channel_listings(
                cleaned_input,
                product_channel_global_id_to_instance_map,
                errors,
                index,
                index_error_map,
            )

        if cleaned_input.get("stocks"):
            cls.clean_stocks(
                cleaned_input,
                warehouse_global_id_to_instance_map,
                errors,
                index,
                index_error_map,
            )

        if base_fields_errors_count > 0 or attributes_errors_count > 0:
            return None
        else:
            return cleaned_input if cleaned_input else None

    @classmethod
    def clean_variants(cls, info, variants, product, errors, index_error_map):
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
            variant_data["product_type"] = product.product_type
            variant_data["product"] = product

            cleaned_input = cls.clean_variant(
                info,
                variant_data,
                product_channel_global_id_to_instance_map,
                warehouse_global_id_to_instance_map,
                used_attribute_values,
                variant_attributes_ids,
                duplicated_sku,
                index_error_map,
                index,
                errors,
            )
            cleaned_inputs_map[index] = cleaned_input

        return cleaned_inputs_map

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
    def save_variants(cls, info, instances_data_with_errors_list, product):
        for instance_data in instances_data_with_errors_list:
            instance = instance_data["instance"]
            if instance:
                cleaned_input = instance_data.pop("cleaned_input")
                cls.save(info, instance_data["instance"], cleaned_input)
                cls.create_variant_stocks(instance, cleaned_input)
                cls.create_variant_channel_listings(instance, cleaned_input)

                if not product.default_variant:
                    product.default_variant = instance
                    product.save(update_fields=["default_variant", "updated_at"])

    @classmethod
    def create_variant_stocks(cls, variant, cleaned_input):
        stocks = cleaned_input.get("stocks")

        if not stocks:
            return

        try:
            warehouse_models.Stock.objects.bulk_create(
                [
                    warehouse_models.Stock(
                        product_variant=variant,
                        warehouse=stock_data["warehouse"],
                        quantity=stock_data["quantity"],
                    )
                    for stock_data in stocks
                ]
            )
        except IntegrityError:
            msg = "Stock for one of warehouses already exists for this product variant."
            raise ValidationError(msg)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        product = cast(
            models.Product,
            cls.get_node_or_error(info, data["product_id"], only_type="Product"),
        )
        error_policy = data["error_policy"]
        errors: dict = defaultdict(list)
        index_error_map: dict = defaultdict(list)

        cleaned_inputs_map = cls.clean_variants(
            info, data["variants"], product, errors, index_error_map
        )
        instances_data_with_errors_list = cls.create_variants(
            info, cleaned_inputs_map, product, errors, index_error_map
        )

        if errors:
            if error_policy == ErrorPolicyEnum.REJECT_EVERYTHING.value:
                results = [
                    ProductVariantBulkResult(
                        product_variant=None, errors=data.get("errors")
                    )
                    for data in instances_data_with_errors_list
                ]
                return ProductVariantBulkCreate(
                    count=0,
                    results=results,
                    errors=validation_error_to_error_type(
                        ValidationError(errors), cls._meta.error_type_class
                    ),
                )

            if error_policy == ErrorPolicyEnum.REJECT_FAILED_ROWS.value:
                for data in instances_data_with_errors_list:
                    if data["errors"] and data["instance"]:
                        data["instance"] = None

        cls.save_variants(info, instances_data_with_errors_list, product)

        instances = [
            ChannelContext(node=instance_data["instance"], channel_slug=None)
            for instance_data in instances_data_with_errors_list
            if instance_data["instance"]
        ]

        # Recalculate the "discounted price" for the parent product
        update_product_discounted_price_task.delay(product.pk)

        update_product_search_vector(product)
        manager = get_plugin_manager_promise(info.context).get()
        transaction.on_commit(
            lambda: [
                manager.product_variant_created(instance.node) for instance in instances
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

        return ProductVariantBulkCreate(
            count=len(instances),
            product_variants=instances,
            results=results,
            errors=validation_error_to_error_type(
                ValidationError(errors), cls._meta.error_type_class
            )
            if errors
            else None,
        )
