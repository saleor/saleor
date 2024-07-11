from collections import defaultdict
from typing import cast

import graphene
from babel.core import get_global
from django.core.exceptions import ValidationError
from django.db.models import F
from graphene.utils.str_converters import to_camel_case

from ....attribute import AttributeType
from ....core.tracing import traced_atomic_transaction
from ....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from ....permission.enums import ProductPermissions
from ....product import models
from ....product.error_codes import ProductVariantBulkErrorCode
from ....warehouse import models as warehouse_models
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...attribute.types import (
    AttributeValueDescriptions,
    AttributeValueSelectableTypeInput,
)
from ...attribute.utils import AttributeAssignmentMixin
from ...channel import ChannelContext
from ...core.descriptions import (
    ADDED_IN_311,
    ADDED_IN_312,
    ADDED_IN_314,
    DEPRECATED_IN_3X_FIELD,
    PREVIEW_FEATURE,
)
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.enums import ErrorPolicyEnum
from ...core.fields import JSONString
from ...core.mutations import (
    BaseMutation,
    ModelMutation,
    validation_error_to_error_type,
)
from ...core.scalars import Date, DateTime
from ...core.types import (
    BaseInputObjectType,
    BaseObjectType,
    BulkProductError,
    NonNullList,
    ProductVariantBulkError,
)
from ...core.utils import get_duplicated_values
from ...core.validators import validate_price_precision
from ...plugins.dataloaders import get_plugin_manager_promise
from ...shop.utils import get_track_inventory_by_default
from ..mutations.channels import ProductVariantChannelListingAddInput
from ..mutations.product.product_create import StockInput
from ..mutations.product_variant.product_variant_create import ProductVariantInput
from ..types import ProductVariant
from ..utils import clean_variant_sku, get_used_variants_attribute_values

CURRENCY_FRACTIONS = get_global("currency_fractions")


def clean_price(
    price,
    field_name,
    currency,
    channel_id,
    variant_index,
    listing_index,
    errors,
    index_error_map,
    path_prefix,
):
    try:
        validate_price_precision(price, currency, CURRENCY_FRACTIONS)
    except ValidationError as error:
        index_error_map[variant_index].append(
            ProductVariantBulkError(
                field=to_camel_case(field_name),
                path=f"{path_prefix}.{listing_index}.{to_camel_case(field_name)}",
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


def get_results(instances_data_with_errors_list, reject_everything=False):
    if reject_everything:
        return [
            ProductVariantBulkResult(product_variant=None, errors=data.get("errors"))
            for data in instances_data_with_errors_list
        ]
    return [
        ProductVariantBulkResult(
            product_variant=ChannelContext(
                node=data.get("instance"), channel_slug=None
            ),
            errors=data.get("errors"),
        )
        if data.get("instance")
        else ProductVariantBulkResult(product_variant=None, errors=data.get("errors"))
        for data in instances_data_with_errors_list
    ]


class ProductVariantBulkResult(BaseObjectType):
    product_variant = graphene.Field(
        ProductVariant, required=False, description="Product variant data."
    )
    errors = NonNullList(
        ProductVariantBulkError,
        required=False,
        description="List of errors occurred on create attempt.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class BulkAttributeValueInput(BaseInputObjectType):
    id = graphene.ID(description="ID of the selected attribute.", required=False)
    external_reference = graphene.String(
        description="External ID of this attribute." + ADDED_IN_314, required=False
    )
    values = NonNullList(
        graphene.String,
        required=False,
        description=(
            "The value or slug of an attribute to resolve. "
            "If the passed value is non-existent, it will be created."
            + DEPRECATED_IN_3X_FIELD
        ),
    )
    dropdown = AttributeValueSelectableTypeInput(
        required=False,
        description="Attribute value ID." + ADDED_IN_312,
    )
    swatch = AttributeValueSelectableTypeInput(
        required=False,
        description="Attribute value ID." + ADDED_IN_312,
    )
    multiselect = NonNullList(
        AttributeValueSelectableTypeInput,
        required=False,
        description="List of attribute value IDs." + ADDED_IN_312,
    )
    numeric = graphene.String(
        required=False,
        description="Numeric value of an attribute." + ADDED_IN_312,
    )
    file = graphene.String(
        required=False,
        description=(
            "URL of the file attribute. Every time, a new value is created."
            + ADDED_IN_312
        ),
    )
    content_type = graphene.String(
        required=False,
        description="File content type." + ADDED_IN_312,
    )
    references = NonNullList(
        graphene.ID,
        description=(
            "List of entity IDs that will be used as references." + ADDED_IN_312
        ),
        required=False,
    )
    rich_text = JSONString(
        required=False,
        description="Text content in JSON format." + ADDED_IN_312,
    )
    plain_text = graphene.String(
        required=False,
        description="Plain text content." + ADDED_IN_312,
    )
    boolean = graphene.Boolean(
        required=False,
        description=(
            "The boolean value of an attribute to resolve. "
            "If the passed value is non-existent, it will be created."
        ),
    )
    date = Date(
        required=False, description=AttributeValueDescriptions.DATE + ADDED_IN_312
    )
    date_time = DateTime(
        required=False, description=AttributeValueDescriptions.DATE_TIME + ADDED_IN_312
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


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

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


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
            description=(
                "Policies of error handling. DEFAULT: "
                + ErrorPolicyEnum.REJECT_EVERYTHING.name
                + ADDED_IN_311
                + PREVIEW_FEATURE
            ),
        )

    class Meta:
        description = "Creates product variants for a given product."
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = BulkProductError
        error_type_field = "bulk_product_errors"
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def clean_attributes(
        cls,
        cleaned_input,
        product_type,
        variant_attributes,
        variant_attributes_ids,
        variant_attributes_external_refs,
        used_attribute_values,
        errors,
        variant_index,
        index_error_map,
    ):
        attributes_errors_count = 0
        if attributes_input := cleaned_input.get("attributes"):
            attributes_ids = {
                attr["id"] for attr in attributes_input if attr.get("id") or []
            }
            attrs_external_refs = {
                attr["external_reference"]
                for attr in attributes_input
                if attr.get("external_reference") or []
            }
            invalid_attributes = attributes_ids - variant_attributes_ids
            invalid_attributes |= attrs_external_refs - variant_attributes_external_refs

            if len(invalid_attributes) > 0:
                message = "Given attributes are not a variant attributes."
                code = ProductVariantBulkErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.value
                index_error_map[variant_index].append(
                    ProductVariantBulkError(
                        field="attributes",
                        path="attributes",
                        message=message,
                        code=code,
                        attributes=invalid_attributes,
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
                    cleaned_attributes = AttributeAssignmentMixin.clean_input(
                        attributes_input, variant_attributes
                    )
                    cleaned_input["attributes"] = cleaned_attributes
                except ValidationError as exc:
                    for error in exc.error_list:
                        attributes = (
                            error.params.get("attributes") if error.params else None
                        )
                        index_error_map[variant_index].append(
                            ProductVariantBulkError(
                                field="attributes",
                                path="attributes",
                                message=error.message,
                                code=error.code,
                                attributes=attributes,
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
                        path="attributes",
                        message=message,
                        code=ProductVariantBulkErrorCode.INVALID.value,
                        attributes=invalid_attributes,
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
    def clean_prices(
        cls,
        price,
        cost_price,
        currency_code,
        channel_id,
        variant_index,
        listing_index,
        errors,
        index_error_map,
        path_prefix,
    ):
        clean_price(
            price,
            "price",
            currency_code,
            channel_id,
            variant_index,
            listing_index,
            errors,
            index_error_map,
            path_prefix,
        )
        clean_price(
            cost_price,
            "cost_price",
            currency_code,
            channel_id,
            variant_index,
            listing_index,
            errors,
            index_error_map,
            path_prefix,
        )

    @classmethod
    def clean_channel_listings(
        cls,
        channel_listings,
        product_channel_global_id_to_instance_map,
        errors,
        variant_index,
        index_error_map,
        path_prefix="channelListings",
    ):
        channel_ids = [
            channel_listing["channel_id"] for channel_listing in channel_listings
        ]
        listings_to_create = []

        duplicates = get_duplicated_values(channel_ids)
        if duplicates:
            if errors is not None:
                errors["channel_listings"] = ValidationError(
                    message="Duplicated channel ID.",
                    code=ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.value,
                    params={"channels": duplicates, "index": variant_index},
                )

        channels_not_assigned_to_product = [
            channel_id
            for channel_id in channel_ids
            if channel_id not in product_channel_global_id_to_instance_map.keys()
        ]

        if channels_not_assigned_to_product:
            code = ProductVariantBulkErrorCode.PRODUCT_NOT_ASSIGNED_TO_CHANNEL.value
            if errors is not None:
                errors["channel_id"].append(
                    ValidationError(
                        message="Product not available in channels.",
                        code=code,
                        params={
                            "index": variant_index,
                            "channels": channels_not_assigned_to_product,
                        },
                    )
                )

        for listing_index, channel_listing in enumerate(channel_listings):
            channel_id = channel_listing["channel_id"]
            errors_count_before_prices = len(index_error_map[variant_index])

            if channel_id in channels_not_assigned_to_product:
                code = ProductVariantBulkErrorCode.PRODUCT_NOT_ASSIGNED_TO_CHANNEL.value
                index_error_map[variant_index].append(
                    ProductVariantBulkError(
                        field="channelId",
                        path=f"{path_prefix}.{listing_index}.channelId",
                        message="Product not available in channels.",
                        code=code,
                        channels=[channel_id],
                    )
                )
                continue

            if channel_id in duplicates:
                index_error_map[variant_index].append(
                    ProductVariantBulkError(
                        field="channelId",
                        path=f"{path_prefix}.{listing_index}.channelId",
                        message="Duplicated channel ID.",
                        code=ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.value,
                        channels=[channel_id],
                    )
                )
                continue

            channel_listing["channel"] = product_channel_global_id_to_instance_map[
                channel_id
            ]
            price = channel_listing.get("price")
            cost_price = channel_listing.get("cost_price")
            currency_code = channel_listing["channel"].currency_code

            cls.clean_prices(
                price,
                cost_price,
                currency_code,
                channel_id,
                variant_index,
                listing_index,
                errors,
                index_error_map,
                path_prefix,
            )

            if len(index_error_map[variant_index]) > errors_count_before_prices:
                continue

            listings_to_create.append(channel_listing)

        return listings_to_create

    @classmethod
    def clean_stocks(
        cls,
        stocks_data,
        warehouse_global_id_to_instance_map,
        errors,
        variant_index,
        index_error_map,
        path_prefix="stocks",
    ):
        stocks_to_create = []
        warehouse_ids = [stock["warehouse"] for stock in stocks_data]

        wrong_warehouse_ids = {
            warehouse_id
            for warehouse_id in warehouse_ids
            if warehouse_id not in warehouse_global_id_to_instance_map.keys()
        }

        if wrong_warehouse_ids:
            if errors is not None:
                errors["warehouses"] = ValidationError(
                    "Not existing warehouse ID.",
                    code=ProductVariantBulkErrorCode.NOT_FOUND.value,
                    params={"warehouses": wrong_warehouse_ids, "index": variant_index},
                )

        duplicates = get_duplicated_values(warehouse_ids)
        if duplicates:
            if errors is not None:
                errors["stocks"] = ValidationError(
                    "Duplicated warehouse ID.",
                    code=ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.value,
                    params={"warehouses": duplicates, "index": variant_index},
                )

        for stock_index, stock_data in enumerate(stocks_data):
            if stock_data["warehouse"] in wrong_warehouse_ids:
                index_error_map[variant_index].append(
                    ProductVariantBulkError(
                        field="warehouses",
                        path=f"{path_prefix}.{stock_index}.warehouse",
                        message="Not existing warehouse ID.",
                        code=ProductVariantBulkErrorCode.NOT_FOUND.value,
                        warehouses=[stock_data["warehouse"]],
                    )
                )
                continue

            if stock_data["warehouse"] in duplicates:
                index_error_map[variant_index].append(
                    ProductVariantBulkError(
                        field="warehouse",
                        path=f"{path_prefix}.{stock_index}.warehouse",
                        message="Duplicated warehouse ID.",
                        code=ProductVariantBulkErrorCode.DUPLICATED_INPUT_ITEM.value,
                        warehouses=[stock_data["warehouse"]],
                    )
                )
                continue

            stock_data["warehouse"] = warehouse_global_id_to_instance_map[
                stock_data["warehouse"]
            ]
            stocks_to_create.append(stock_data)

        return stocks_to_create

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
                        path=to_camel_case(key),
                        message=e.messages[0],
                        code=e.code,
                    )
                )
            error_dict[key].extend(value)

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
                metadata_list = cleaned_input.pop("metadata", None)
                private_metadata_list = cleaned_input.pop("private_metadata", None)
                instance = models.ProductVariant()
                cleaned_input["product"] = product
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
                    path="weight",
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
                    path="quantity_limit_per_customer",
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
                ProductVariantBulkError(
                    field="sku", path="sku", message=message, code=code
                )
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
        variant_attributes,
        used_attribute_values,
        variant_attributes_ids,
        variant_attributes_external_refs,
        duplicated_sku,
        index_error_map,
        index,
        errors,
    ):
        cleaned_input = ModelMutation.clean_input(
            info, None, variant_data, input_cls=ProductVariantBulkCreateInput
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
            variant_attributes,
            variant_attributes_ids,
            variant_attributes_external_refs,
            used_attribute_values,
            errors,
            index,
            index_error_map,
        )

        if listings_data := cleaned_input.get("channel_listings"):
            cleaned_input["channel_listings"] = cls.clean_channel_listings(
                listings_data,
                product_channel_global_id_to_instance_map,
                errors,
                index,
                index_error_map,
            )

        if stocks_data := cleaned_input.get("stocks"):
            cleaned_input["stocks"] = cls.clean_stocks(
                stocks_data,
                warehouse_global_id_to_instance_map,
                errors,
                index,
                index_error_map,
            )

        if base_fields_errors_count > 0 or attributes_errors_count > 0:
            return None

        return cleaned_input if cleaned_input else None

    @classmethod
    def clean_variants(cls, info, variants, product, errors, index_error_map):
        cleaned_inputs_map = {}
        product_type = product.product_type

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

        variant_attributes = product_type.variant_attributes.annotate(
            variant_selection=F("attributevariant__variant_selection")
        )
        variant_attributes_ids = {
            graphene.Node.to_global_id("Attribute", variant_attribute.id)
            for variant_attribute in variant_attributes
        }
        variant_attributes_external_refs = {
            variant_attribute.external_reference
            for variant_attribute in variant_attributes
        }
        used_attribute_values = get_used_variants_attribute_values(product)

        duplicated_sku = get_duplicated_values(
            [variant.sku for variant in variants if variant.sku]
        )

        for index, variant_data in enumerate(variants):
            variant_data["product_type"] = product_type
            variant_data["product"] = product

            cleaned_input = cls.clean_variant(
                info,
                variant_data,
                product_channel_global_id_to_instance_map,
                warehouse_global_id_to_instance_map,
                variant_attributes,
                used_attribute_values,
                variant_attributes_ids,
                variant_attributes_external_refs,
                duplicated_sku,
                index_error_map,
                index,
                errors,
            )
            cleaned_inputs_map[index] = cleaned_input

        return cleaned_inputs_map

    @classmethod
    def prepare_channel_listings(cls, variant, listings_input, listings_to_create):
        listings_to_create += [
            models.ProductVariantChannelListing(
                channel=listing_data["channel"],
                variant=variant,
                price_amount=listing_data["price"],
                # set the discounted price the same as price for now, the discounted
                # value will be calculated asynchronously in the celery task
                discounted_price_amount=listing_data["price"],
                cost_price_amount=listing_data.get("cost_price"),
                currency=listing_data["channel"].currency_code,
                preorder_quantity_threshold=listing_data.get("preorder_threshold"),
            )
            for listing_data in listings_input
        ]

    @classmethod
    def set_variant_name(cls, variant, cleaned_input):
        attributes_input = cleaned_input.get("attributes", [])
        sku = cleaned_input.get("sku")
        attributes_display: list = []

        for attribute_data in attributes_input:
            if (
                attribute_data[0].type == AttributeType.PRODUCT_TYPE
                and attribute_data[0].variant_selection
            ):
                attributes_display.append(
                    ", ".join([value for value in attribute_data[1].values])
                )

        name = " / ".join(sorted(attributes_display))
        if not name:
            name = sku or variant.get_global_id()

        variant.name = name

    @classmethod
    @traced_atomic_transaction()
    def save_variants(cls, info, variants_data_with_errors_list, product):
        variants_to_create: list = []
        stocks_to_create: list = []
        listings_to_create: list = []
        attributes_to_save: list = []

        for variant_data in variants_data_with_errors_list:
            variant = variant_data["instance"]

            if not variant:
                continue
            track_inventory_by_default = get_track_inventory_by_default(info)
            track_inventory = variant_data["cleaned_input"].get("track_inventory")
            if track_inventory_by_default is not None:
                variant.track_inventory = (
                    track_inventory_by_default
                    if track_inventory is None
                    else track_inventory
                )
            variants_to_create.append(variant)
            cleaned_input = variant_data["cleaned_input"]

            if stocks_input := cleaned_input.get("stocks"):
                cls.prepare_stocks(variant, stocks_input, stocks_to_create)

            if listings_input := cleaned_input.get("channel_listings"):
                cls.prepare_channel_listings(
                    variant, listings_input, listings_to_create
                )

            if attributes := cleaned_input.get("attributes"):
                attributes_to_save.append((variant, attributes))

            if not variant.name:
                cls.set_variant_name(variant, cleaned_input)
        models.ProductVariant.objects.bulk_create(variants_to_create)

        for variant, attributes in attributes_to_save:
            AttributeAssignmentMixin.save(variant, attributes)

        warehouse_models.Stock.objects.bulk_create(stocks_to_create)
        models.ProductVariantChannelListing.objects.bulk_create(listings_to_create)

        if product and not product.default_variant and variants_to_create:
            product.default_variant = variants_to_create[0]
            product.save(update_fields=["default_variant", "updated_at"])

        return variants_to_create

    @classmethod
    def prepare_stocks(cls, variant, stocks_input, stocks_to_create):
        stocks_to_create += [
            warehouse_models.Stock(
                product_variant=variant,
                warehouse=stock_data["warehouse"],
                quantity=stock_data["quantity"],
            )
            for stock_data in stocks_input
        ]

    @classmethod
    def post_save_actions(cls, info, instances, product):
        variant_ids = set([instance.node.id for instance in instances])
        channel_ids = set(
            models.ProductVariantChannelListing.objects.filter(
                variant_id__in=variant_ids
            ).values_list("channel_id", flat=True)
        )
        # This will finally recalculate discounted prices for products.
        cls.call_event(mark_active_catalogue_promotion_rules_as_dirty, channel_ids)

        product.search_index_dirty = True
        product.save(update_fields=["search_index_dirty"])

        webhooks = get_webhooks_for_event(WebhookEventAsyncType.PRODUCT_VARIANT_CREATED)
        manager = get_plugin_manager_promise(info.context).get()
        for instance in instances:
            cls.call_event(
                manager.product_variant_created, instance.node, webhooks=webhooks
            )

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        product = cast(
            models.Product,
            cls.get_node_or_error(info, data["product_id"], only_type="Product"),
        )
        error_policy = data.get("error_policy", ErrorPolicyEnum.REJECT_EVERYTHING.value)
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
                results = get_results(instances_data_with_errors_list, True)
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

        # prepare and return data
        results = get_results(instances_data_with_errors_list)
        instances = [
            result.product_variant for result in results if result.product_variant
        ]
        cls.post_save_actions(info, instances, product)

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
