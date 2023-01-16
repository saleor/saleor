from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.utils import IntegrityError
from graphene.types import InputObjectType
from graphene.utils.str_converters import to_camel_case

from ....core.permissions import ProductPermissions
from ....core.tracing import traced_atomic_transaction
from ....product import models
from ....product.error_codes import ProductErrorCode
from ....product.search import update_product_search_vector
from ....product.tasks import update_product_discounted_price_task
from ....product.utils.variants import generate_and_set_variant_name
from ....warehouse import models as warehouse_models
from ...attribute.utils import AttributeAssignmentMixin
from ...channel import ChannelContext
from ...channel.types import Channel
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
    product_variant = graphene.Field(ProductVariant, required=False)
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
        description="List of the created variants.",
    )

    results = NonNullList(
        ProductVariantBulkResult,
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
        error_policy = ErrorPolicyEnum(
            required=False,
            default_value=ErrorPolicyEnum.REJECT_EVERYTHING.name,
            description="Policies of error handling.",
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
        warehouses,
        errors: dict,
        variant_index: int,
        index_error_map: dict,
    ):
        cleaned_input = ModelMutation.clean_input(
            info, instance, data, input_cls=ProductVariantBulkCreateInput
        )

        product = instance.product if instance else data["product"]
        attributes = cleaned_input.get("attributes")
        if attributes:
            try:
                cleaned_input["attributes"] = ProductVariantCreate.clean_attributes(
                    attributes, data["product_type"]
                )
            except ValidationError as exc:
                index_error_map[variant_index].append(
                    ProductVariantBulkError(
                        field="attributes", message=exc.message, code=exc.code
                    )
                )
                exc.params = {"index": variant_index}
                errors["attributes"] = exc

        channel_listings = cleaned_input.get("channel_listings")
        if channel_listings:
            cleaned_input["channel_listings"] = cls.clean_channel_listings(
                channel_listings, errors, product, variant_index, index_error_map
            )

        stocks = cleaned_input.get("stocks")
        if stocks:
            cls.clean_stocks(stocks, warehouses, errors, variant_index, index_error_map)

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
            error.code = ProductErrorCode.INVALID.value
            error.params = {
                "channels": [channel_id],
                "index": variant_index,
            }
            errors[field_name].append(error)
            index_error_map[variant_index].append(
                ProductVariantBulkError(
                    field=to_camel_case(field_name),
                    message=error.message,
                    code=ProductErrorCode.INVALID.value,
                    channels=[channel_id],
                )
            )

    @classmethod
    def clean_channel_listings(
        cls, channels_data, errors, product, variant_index, index_error_map
    ):
        channel_ids = [
            channel_listing["channel_id"] for channel_listing in channels_data
        ]
        duplicates = get_duplicated_values(channel_ids)
        if duplicates:
            message = "Duplicated channel ID."
            index_error_map[variant_index].append(
                ProductVariantBulkError(
                    field="channelListings",
                    message=message,
                    code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
                    channels=duplicates,
                )
            )
            errors["channel_listings"] = ValidationError(
                message=message,
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
            message = "Product not available in channels."
            index_error_map[variant_index].append(
                ProductVariantBulkError(
                    field="channelId",
                    message=message,
                    code=ProductErrorCode.PRODUCT_NOT_ASSIGNED_TO_CHANNEL.value,
                    channels=channels_not_assigned_to_product,
                )
            )
            errors["channel_id"].append(
                ValidationError(
                    message=message,
                    code=ProductErrorCode.PRODUCT_NOT_ASSIGNED_TO_CHANNEL.value,
                    params={
                        "index": variant_index,
                        "channels": channels_not_assigned_to_product,
                    },
                )
            )
        return channels_data

    @classmethod
    def clean_stocks(
        cls, stocks_data, warehouses, errors, variant_index, index_error_map
    ):
        warehouse_ids = [stock["warehouse"] for stock in stocks_data]

        warehouse_global_id_to_instance_map = {
            graphene.Node.to_global_id("Warehouse", warehouse.id): warehouse
            for warehouse in warehouses
        }

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
                    code=ProductErrorCode.NOT_FOUND.value,
                    warehouses=wrong_warehouse_ids,
                )
            )
            errors["warehouses"] = ValidationError(
                message,
                code=ProductErrorCode.NOT_FOUND.value,
                params={"warehouses": wrong_warehouse_ids, "index": variant_index},
            )

        duplicates = get_duplicated_values(warehouse_ids)
        if duplicates:
            message = "Duplicated warehouse ID."
            index_error_map[variant_index].append(
                ProductVariantBulkError(
                    field="stocks",
                    message=message,
                    code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
                    warehouses=duplicates,
                )
            )
            errors["stocks"] = ValidationError(
                message,
                code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
                params={"warehouses": duplicates, "index": variant_index},
            )

        if not duplicates and not wrong_warehouse_ids:
            for stock_data in stocks_data:
                stock_data["warehouse"] = warehouse_global_id_to_instance_map[
                    stock_data["warehouse"]
                ]

    @classmethod
    def add_indexes_to_errors(cls, index, error, error_dict, index_error_map):
        """Append errors with index in params to mutation error dict."""
        for key, value in error.error_dict.items():
            for e in value:
                if e.params:
                    e.params["index"] = index
                else:
                    e.params = {"index": index}
            error_dict[key].extend(value)
            index_error_map[index].append(
                ProductVariantBulkError(
                    field=to_camel_case(key),
                    message=e.message,
                    code=e.code,
                )
            )

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()

        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)
            if not instance.name:
                generate_and_set_variant_name(instance, cleaned_input.get("sku"))

    @classmethod
    def create_variants(cls, info, cleaned_inputs, product, errors, index_error_map):
        instances = []
        qwe = []

        for index, cleaned_input in enumerate(cleaned_inputs):
            if not cleaned_input:
                qwe.append({"instance": None, "errors": index_error_map[index]})
                continue
            try:
                instance = models.ProductVariant()
                cleaned_input["product"] = product
                instance = cls.construct_instance(instance, cleaned_input)
                cls.clean_instance(info, instance)
                instances.append(instance)
                qwe.append({"instance": instance, "errors": index_error_map[index]})
            except ValidationError as exc:
                cls.add_indexes_to_errors(index, exc, errors, index_error_map)
                qwe.append({"instance": None, "errors": index_error_map[index]})
        return instances, qwe

    @classmethod
    def validate_duplicated_sku(cls, sku, index, sku_list, errors, index_error_map):
        if sku in sku_list:
            message = "Duplicated SKU."
            index_error_map[index].append(
                ProductVariantBulkError(
                    field="sku", message=message, code=ProductErrorCode.UNIQUE
                )
            )
            errors["sku"].append(
                ValidationError(
                    message, ProductErrorCode.UNIQUE, params={"index": index}
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
    def clean_variants(cls, info, variants, product, errors, index_error_map):
        cleaned_inputs = []
        sku_list = []
        warehouses = warehouse_models.Warehouse.objects.all()
        used_attribute_values = get_used_variants_attribute_values(product)

        for index, variant_data in enumerate(variants):
            if variant_data.attributes:
                try:
                    cls.validate_duplicated_attribute_values(
                        variant_data.attributes, used_attribute_values
                    )
                except ValidationError as exc:
                    index_error_map[index].append(
                        ProductVariantBulkError(
                            field="attributes", message=exc.message, code=exc.code
                        )
                    )
                    errors["attributes"].append(
                        ValidationError(exc.message, exc.code, params={"index": index})
                    )

            variant_data["product_type"] = product.product_type
            variant_data["product"] = product
            cleaned_input = cls.clean_variant_input(
                info, None, variant_data, warehouses, errors, index, index_error_map
            )

            cleaned_inputs.append(cleaned_input if cleaned_input else None)

            if cleaned_input["sku"]:
                cls.validate_duplicated_sku(
                    cleaned_input["sku"], index, sku_list, errors, index_error_map
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
        product = cls.get_node_or_error(info, data["product_id"], only_type="Product")

        error_policy = data["error_policy"]
        errors = defaultdict(list)  # deprecated
        index_error_map = defaultdict(list)

        cleaned_inputs = cls.clean_variants(
            info, data["variants"], product, errors, index_error_map
        )

        instances, qwe = cls.create_variants(
            info, cleaned_inputs, product, errors, index_error_map
        )

        if errors and error_policy == ErrorPolicyEnum.REJECT_EVERYTHING.name:
            results = [
                ProductVariantBulkResult(product_variant=None, errors=ff.get("errors"))
                for ff in qwe
            ]

            return ProductVariantBulkCreate(
                count=0,
                results=results,
                errors=validation_error_to_error_type(
                    ValidationError(errors), cls._meta.error_type_class
                ),
            )

        cls.save_variants(info, instances, product, cleaned_inputs)

        # Recalculate the "discounted price" for the parent product
        update_product_discounted_price_task.delay(product.pk)

        instances = [
            ChannelContext(node=instance, channel_slug=None) for instance in instances
        ]

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
                    node=ff.get("instance"), channel_slug=None
                ),
                errors=ff.get("errors"),
            )
            for ff in qwe
        ]

        return ProductVariantBulkCreate(
            count=len(instances),
            product_variants=instances,
            results=results,
            errors=validation_error_to_error_type(
                ValidationError(errors), cls._meta.error_type_class
            ),
        )
