from collections import defaultdict
from datetime import datetime

import graphene
import pytz
import requests
from django.core.exceptions import ValidationError
from django.core.files import File

from ....core.permissions import ProductPermissions
from ....core.tracing import traced_atomic_transaction
from ....core.utils.editorjs import clean_editor_js
from ....core.utils.validators import get_oembed_data
from ....product import ProductMediaTypes, models
from ....product.error_codes import ProductErrorCode
from ....product.utils.variants import generate_and_set_variant_name
from ....warehouse.models import Stock, Warehouse
from ...attribute.utils import AttributeAssignmentMixin
from ...channel import ChannelContext
from ...core.enums import ErrorPolicyEnum
from ...core.mutations import BaseMutation, ModelMutation
from ...core.types import BulkProductError, MediaInput, NonNullList
from ...core.utils import get_duplicated_values
from ...core.validators import clean_seo_fields, validate_price_precision
from ...core.validators.file import (
    clean_image_file,
    get_filename_from_url,
    is_image_url,
    validate_image_url,
)
from ...plugins.dataloaders import load_plugin_manager
from ..mutations.channels import ProductChannelListingCreateInput
from ..mutations.product.product_create import ProductCreateInput
from ..types import Product
from ..utils import clean_variant_sku
from .product_variant_bulk_create import ProductVariantBulkCreateInput


class ProductBulkResult(graphene.ObjectType):
    product = graphene.Field(Product, required=True)
    errors = graphene.Field(BulkProductError)


class ProductBulkCreateInput(ProductCreateInput):
    media = NonNullList(MediaInput, required=False)
    channel_listings = NonNullList(ProductChannelListingCreateInput, required=False)
    variants = NonNullList(
        ProductVariantBulkCreateInput,
        required=False,
        description="Input list of product variants to create.",
    )


class ProductBulkCreate(BaseMutation):
    count = graphene.Int(
        required=True,
        description="Returns how many objects were created.",
    )
    results = NonNullList(
        ProductBulkResult,
        required=True,
        default_value=[],
        description="List of the created products.",
    )

    class Arguments:
        products = NonNullList(
            ProductBulkCreateInput,
            required=True,
            description="Input list of products to create.",
        )
        error_policy = ErrorPolicyEnum(
            required=False,
            default_value=ErrorPolicyEnum.REJECT_EVERYTHING.name,
            description="Policies of error handling.",
        )

    class Meta:
        description = "Creates products."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = BulkProductError
        error_type_field = "bulk_product_errors"
        support_meta_field = True
        support_private_meta_field = True

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
    def clean_weight(cls, cleaned_input, product_index, errors):
        weight = cleaned_input.get("weight")
        if weight and weight.value < 0:
            exc = ValidationError(
                {
                    "weight": ValidationError(
                        "Product can't have negative weight.",
                        code=ProductErrorCode.INVALID.value,
                    )
                }
            )
            exc.params = {"index": product_index}
            errors["weight"] = exc

    @staticmethod
    def _clean_attributes(attributes: dict, product_type: models.ProductType):
        attributes_qs = product_type.product_attributes.all()
        attributes = AttributeAssignmentMixin.clean_input(attributes, attributes_qs)
        return attributes

    @classmethod
    def clean_product_attributes(cls, cleaned_input, product_index, errors):
        if attributes := cleaned_input.get("attributes"):
            try:
                cleaned_input["attributes"] = cls._clean_attributes(
                    attributes, cleaned_input["product_type"]
                )
            except ValidationError as exc:
                exc.params = {"index": product_index}
                errors["attributes"] = exc

    @classmethod
    def _clean_channel_listing(
        cls, channel_listings_input, channels_global_ids, object_index, errors
    ):
        channel_listings_input_global_ids = [
            channel_listing["channel_id"] for channel_listing in channel_listings_input
        ]

        wrong_channel_ids = {
            channel_id
            for channel_id in channel_listings_input_global_ids
            if channel_id not in channels_global_ids
        }
        if wrong_channel_ids:
            errors["channel_listings"] = ValidationError(
                "Not existing channel ID.",
                code=ProductErrorCode.NOT_FOUND.value,
                params={"channels": wrong_channel_ids, "index": object_index},
            )

        duplicates = get_duplicated_values(channel_listings_input_global_ids)
        if duplicates:
            errors["channel_listings"] = ValidationError(
                "Duplicated channel ID.",
                code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
                params={"channels": duplicates, "index": object_index},
            )

        return duplicates, wrong_channel_ids

    @staticmethod
    def set_available_for_purchase_at(
        is_available_for_purchase, available_for_purchase_at, channel_data
    ):
        if is_available_for_purchase is False:
            channel_data["available_for_purchase_at"] = None
        elif is_available_for_purchase is True and not available_for_purchase_at:
            channel_data["available_for_purchase_at"] = datetime.now(pytz.UTC)
        else:
            channel_data["available_for_purchase_at"] = available_for_purchase_at

    @staticmethod
    def set_published_at(channel_data):
        if channel_data.get("is_published") and not channel_data.get("published_at"):
            channel_data["published_at"] = datetime.now(pytz.UTC)

    @classmethod
    def clean_product_channel_listings(
        cls, cleaned_input, channels, product_index, errors
    ):
        if channels_data := cleaned_input.get("channel_listings"):
            channel_global_id_to_instance_map = {
                graphene.Node.to_global_id("Channel", channel.id): channel
                for channel in channels
            }

            duplicates, wrong_channel_ids = cls._clean_channel_listing(
                channels_data,
                channel_global_id_to_instance_map.keys(),
                product_index,
                errors,
            )
            if not duplicates and not wrong_channel_ids:
                invalid_available_for_purchase = []

                for channel_data in channels_data:
                    is_available_for_purchase = channel_data.pop(
                        "is_available_for_purchase", None
                    )
                    available_for_purchase_at = channel_data.get(
                        "available_for_purchase_at"
                    )

                    if is_available_for_purchase is False and available_for_purchase_at:
                        invalid_available_for_purchase.append(
                            channel_data["channel_id"]
                        )

                    if invalid_available_for_purchase:
                        error_msg = (
                            "Cannot set available for purchase at when"
                            " isAvailableForPurchase is false."
                        )
                        errors["channel_listings"] = ValidationError(
                            error_msg,
                            code=ProductErrorCode.NOT_FOUND.value,
                            params={
                                "channels": invalid_available_for_purchase,
                                "index": product_index,
                            },
                        )
                        continue

                    channel = channel_global_id_to_instance_map[
                        channel_data["channel_id"]
                    ]
                    channel_data["channel"] = channel
                    channel_data["currency"] = channel.currency_code
                    cls.set_published_at(channel_data)

                    if is_available_for_purchase is not None:
                        cls.set_available_for_purchase_at(
                            is_available_for_purchase,
                            available_for_purchase_at,
                            channel_data,
                        )

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
    def clean_variant_channel_listing(
        cls,
        cleaned_input,
        channels,
        channels_assigned_to_product,
        variant_index,
        errors,
    ):
        if channels_data := cleaned_input.get("channel_listings"):
            channel_global_id_to_instance_map = {
                graphene.Node.to_global_id("Channel", channel.id): channel
                for channel in channels
            }

            duplicates, wrong_channel_ids = cls._clean_channel_listing(
                channels_data,
                channel_global_id_to_instance_map.keys(),
                variant_index,
                errors,
            )

            if not duplicates and not wrong_channel_ids:
                channels_not_assigned_to_product = []

                for channel_data in channels_data:
                    channel_id = channel_data["channel_id"]
                    channel = channel_global_id_to_instance_map[
                        channel_data["channel_id"]
                    ]
                    currency_code = channel.currency_code

                    channel_data["channel"] = channel
                    channel_data["currency"] = currency_code

                    price = channel_data.get("price")
                    cost_price = channel_data.get("cost_price")

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

                    if channel_id not in channels_assigned_to_product:
                        channels_not_assigned_to_product.append(channel_id)

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

    @classmethod
    def clean_media(cls, cleaned_input, product_index, errors):
        if media_inputs := cleaned_input.get("media"):
            for media_input in media_inputs:
                image = media_input.get("image")
                media_url = media_input.get("media_url")

                if not image and not media_url:
                    exc = ValidationError(
                        {
                            "media": ValidationError(
                                "Image or external URL is required.",
                                code=ProductErrorCode.REQUIRED,
                            )
                        }
                    )
                    exc.params = {"index": product_index}
                    errors["media"] = exc

                if image and media_url:
                    exc = ValidationError(
                        {
                            "media": ValidationError(
                                "Either image or external URL is required.",
                                code=ProductErrorCode.DUPLICATED_INPUT_ITEM,
                            )
                        }
                    )
                    exc.params = {"index": product_index}
                    errors["media"] = exc

    @classmethod
    def clean_stocks(cls, cleaned_input, warehouses, errors, variant_index):
        if stocks_data := cleaned_input.get("stocks"):
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
                errors["warehouses"] = ValidationError(
                    "Not existing warehouse ID.",
                    code=ProductErrorCode.NOT_FOUND.value,
                    params={"warehouses": wrong_warehouse_ids, "index": variant_index},
                )

            duplicates = get_duplicated_values(warehouse_ids)
            if duplicates:
                errors["warehouses"] = ValidationError(
                    "Duplicated warehouse ID.",
                    code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
                    params={"warehouses": duplicates, "index": variant_index},
                )

            if not duplicates and not wrong_warehouse_ids:
                for stock_data in stocks_data:
                    stock_data["warehouse"] = warehouse_global_id_to_instance_map[
                        stock_data["warehouse"]
                    ]

    @classmethod
    def clean_variant_input(
        cls,
        info,
        data: dict,
        product_type,
        channels,
        channels_assigned_to_product,
        warehouses,
        variant_index: int,
        errors: dict,
    ):
        cleaned_input = ModelMutation.clean_input(
            info, None, data, input_cls=ProductVariantBulkCreateInput
        )

        if attributes := cleaned_input.get("attributes"):
            try:
                cleaned_input["attributes"] = cls._clean_attributes(
                    attributes, product_type
                )
            except ValidationError as exc:
                exc.params = {"index": variant_index}
                errors["attributes"] = exc

        cls.clean_variant_channel_listing(
            cleaned_input, channels, channels_assigned_to_product, variant_index, errors
        )
        cls.clean_stocks(cleaned_input, warehouses, errors, variant_index)

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
    def validate_duplicated_sku(cls, sku, index, sku_list, errors):
        if sku in sku_list:
            errors["sku"].append(
                ValidationError(
                    "Duplicated SKU.", ProductErrorCode.UNIQUE, params={"index": index}
                )
            )
        sku_list.append(sku)

    @classmethod
    def clean_variants(
        cls, info, cleaned_input, channels, warehouses, sku_list, product_index, errors
    ):
        cleaned_variants_inputs = []
        variants_errors = defaultdict(list)
        product_type = cleaned_input.get("product_type")
        channels_assigned_to_product = [
            channel_listing["channel_id"]
            for channel_listing in cleaned_input.get("channel_listings", [])
        ]
        if variants := cleaned_input.get("variants"):
            for variant_index, variant_data in enumerate(variants):
                cleaned_variant_input = cls.clean_variant_input(
                    info,
                    variant_data,
                    product_type,
                    channels,
                    channels_assigned_to_product,
                    warehouses,
                    variant_index,
                    variants_errors,
                )

                cleaned_variants_inputs.append(
                    cleaned_variant_input if cleaned_variant_input else None
                )

                if cleaned_variant_input["sku"]:
                    cls.validate_duplicated_sku(
                        variant_data["sku"], variant_index, sku_list, variants_errors
                    )

            cleaned_input["variants"] = cleaned_variants_inputs

    @classmethod
    def clean_product_input(
        cls,
        info,
        data: dict,
        channels,
        warehouses,
        sku_list,
        product_index: int,
        errors: dict,
    ):
        try:
            cleaned_input = ModelMutation.clean_input(
                info, None, data, input_cls=ProductBulkCreateInput
            )
        except ValidationError as exc:
            exc.params = {"index": product_index}
            errors["field"] = exc

        description = cleaned_input.get("description")
        cleaned_input["description_plaintext"] = (
            clean_editor_js(description, to_string=True) if description else ""
        )

        cls.clean_weight(cleaned_input, product_index, errors)
        cls.clean_media(cleaned_input, product_index, errors)
        cls.clean_product_attributes(cleaned_input, product_index, errors)
        cls.clean_product_channel_listings(
            cleaned_input, channels, product_index, errors
        )
        cls.clean_variants(
            info, cleaned_input, channels, warehouses, sku_list, product_index, errors
        )

        if "tax_code" in cleaned_input:
            manager = load_plugin_manager(info.context)
            manager.assign_tax_code_to_object_meta(None, cleaned_input["tax_code"])

        clean_seo_fields(cleaned_input)
        return cleaned_input

    @classmethod
    def clean_products(cls, info, products_data, channels, warehouses, errors):
        cleaned_inputs = []
        sku_list = []
        for product_index, product_data in enumerate(products_data):
            cleaned_input = cls.clean_product_input(
                info,
                product_data,
                channels,
                warehouses,
                sku_list,
                product_index,
                errors,
            )
            cleaned_inputs.append(cleaned_input if cleaned_input else None)
        return cleaned_inputs

    @classmethod
    def create_products(cls, info, cleaned_inputs, errors):
        instances = []
        for index, cleaned_input in enumerate(cleaned_inputs):
            if not cleaned_input:
                continue
            try:
                metadata_list = cleaned_input.pop("metadata", None)
                private_metadata_list = cleaned_input.pop("private_metadata", None)

                instance = models.Product()
                instance = cls.construct_instance(instance, cleaned_input)
                cls.validate_and_update_metadata(
                    instance, metadata_list, private_metadata_list
                )
                cls.clean_instance(info, instance)
                instances.append(instance)

                # assign product instance to media data
                if media := cleaned_input.get("media"):
                    for media_input in media:
                        media_input["product"] = instance

                # assign product instance to variants data
                if variants := cleaned_input.get("variants"):
                    for variant in variants:
                        variant["product"] = instance

                # assign product instance to channel listings data
                if channel_listings := cleaned_input.get("channel_listings"):
                    for channel_listing in channel_listings:
                        channel_listing["product"] = instance

            except ValidationError as exc:
                cls.add_indexes_to_errors(index, exc, errors)
        return instances

    @classmethod
    def create_variants(cls, variants_inputs):
        variants_instances_data = []
        for variant_input in variants_inputs:
            instance = models.ProductVariant()
            instance = cls.construct_instance(instance, variant_input)

            if not instance.name:
                generate_and_set_variant_name(instance, variant_input.get("sku"))

            # store variant related objects data to create related objects
            # after variant instance will be created
            related_data = {
                "attributes": variant_input.get("attributes"),
                "channel_listings": variant_input.get("channel_listings"),
                "stocks": variant_input.get("stocks"),
            }
            variants_instances_data.append((instance, related_data))

        return variants_instances_data

    @classmethod
    def save_attributes(cls, instance, cleaned_input):
        if attributes := cleaned_input.get("attributes"):
            AttributeAssignmentMixin.save(instance, attributes)

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info, products_instances, cleaned_inputs):
        assert len(products_instances) == len(
            cleaned_inputs
        ), "There should be the same number of instances and cleaned inputs."

        new_variants = []
        updated_channels = set()

        for product, cleaned_input in zip(products_instances, cleaned_inputs):
            product.save()
            cls.save_media(info, product, cleaned_input)
            cls.save_attributes(product, cleaned_input)
            cls.save_products_channel_listings(product, cleaned_input, updated_channels)
            cls.save_variants(cleaned_input, new_variants, updated_channels)

        return new_variants, updated_channels

    @classmethod
    def save_products_channel_listings(cls, product, cleaned_input, updated_channels):
        if channel_listings := cleaned_input.get("channel_listings"):
            models.ProductChannelListing.objects.bulk_create(
                [
                    models.ProductChannelListing(
                        product=product,
                        channel=channel_listing["channel"],
                        currency=channel_listing["channel"].currency_code,
                        is_published=channel_listing.get("is_published", False),
                        published_at=channel_listing.get("published_at"),
                        visible_in_listings=channel_listing.get(
                            "visible_in_listings", False
                        ),
                        available_for_purchase_at=channel_listing.get(
                            "available_for_purchase_at"
                        ),
                    )
                    for channel_listing in channel_listings
                ]
            )
            updated_channels.update(
                {channel_listing["channel"] for channel_listing in channel_listings}
            )

    @classmethod
    def save_variants_channel_listings(
        cls, variant, related_objects_data, updated_channels
    ):
        if channel_listings := related_objects_data.get("channel_listings"):
            models.ProductVariantChannelListing.objects.bulk_create(
                [
                    models.ProductVariantChannelListing(
                        channel=channel_listing["channel"],
                        variant=variant,
                        price_amount=channel_listing["price"],
                        cost_price_amount=channel_listing.get("cost_price"),
                        currency=channel_listing["channel"].currency_code,
                        preorder_quantity_threshold=channel_listing.get(
                            "preorder_threshold"
                        ),
                    )
                    for channel_listing in channel_listings
                ]
            )
            updated_channels.update(
                {channel_listing["channel"] for channel_listing in channel_listings}
            )

    @classmethod
    def save_stocks(cls, variant, related_objects_data):
        if stocks_data := related_objects_data.get("stocks"):
            Stock.objects.bulk_create(
                [
                    Stock(
                        product_variant=variant,
                        warehouse=stock_data["warehouse"],
                        quantity=stock_data["quantity"],
                    )
                    for stock_data in stocks_data
                ]
            )

    @classmethod
    def save_variants(cls, cleaned_input, new_variants, updated_channels):
        if variants_input := cleaned_input.get("variants"):
            variants_and_related_data = cls.create_variants(variants_input)
            models.ProductVariant.objects.bulk_create(
                [variant_data[0] for variant_data in variants_and_related_data]
            )

            for variant_data in variants_and_related_data:
                variant = variant_data[0]
                related_objects_data = variant_data[1]

                cls.save_attributes(variant, related_objects_data)
                cls.save_variants_channel_listings(
                    variant, related_objects_data, updated_channels
                )
                cls.save_stocks(variant, related_objects_data)
                new_variants.append(variant)

    @classmethod
    def save_media(cls, info, product, cleaned_input):
        if media_inputs := cleaned_input.get("media"):
            product_media_instances = []
            for media_input in media_inputs:
                alt = media_input.get("alt", "")
                media_url = media_input.get("media_url")
                if img_data := media_input.get("image"):
                    media_input["image"] = info.context.FILES.get(img_data)
                    image_data = clean_image_file(
                        media_input, "image", ProductErrorCode
                    )
                    product_media_instances.append(
                        models.ProductMedia(
                            image=image_data,
                            alt=alt,
                            product=product,
                            type=ProductMediaTypes.IMAGE,
                        )
                    )
                if media_url:
                    if is_image_url(media_url):
                        validate_image_url(
                            media_url, "media_url", ProductErrorCode.INVALID
                        )
                        filename = get_filename_from_url(media_url)
                        image_data = requests.get(media_url, stream=True)
                        image_data = File(image_data.raw, filename)
                        product_media_instances.append(
                            models.ProductMedia(
                                image=image_data,
                                alt=alt,
                                product=product,
                                type=ProductMediaTypes.IMAGE,
                            )
                        )
                    else:
                        oembed_data, media_type = get_oembed_data(
                            media_url, "media_url"
                        )
                        product_media_instances.append(
                            models.ProductMedia(
                                external_url=oembed_data["url"],
                                alt=oembed_data.get("title", alt),
                                product=product,
                                type=media_type,
                                oembed_data=oembed_data,
                            )
                        )
            models.ProductMedia.objects.bulk_create(product_media_instances)

    @classmethod
    def send_events(cls, info, products, variants, channels):
        manager = load_plugin_manager(info.context)
        for product in products:
            cls.call_event(manager.product_created, product)

        for variant in variants:
            cls.call_event(manager.product_variant_created, variant)

        for channel in channels:
            cls.call_event(manager.channel_updated, channel)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        errors = defaultdict(list)
        data.pop("error_policy")

        channels = models.Channel.objects.all()
        warehouses = Warehouse.objects.all()

        cleaned_inputs = cls.clean_products(
            info, data["products"], channels, warehouses, errors
        )

        products_instances = cls.create_products(info, cleaned_inputs, errors)

        if errors:
            raise ValidationError(errors)

        new_variants, updated_channels = cls.save(
            info, products_instances, cleaned_inputs
        )

        products = [
            ChannelContext(node=instance, channel_slug=None)
            for instance in products_instances
        ]

        cls.send_events(info, products, new_variants, updated_channels)

        return ProductBulkCreate(
            count=len(products),
            results=[ProductBulkResult(product=product) for product in products],
        )
