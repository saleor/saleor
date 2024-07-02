from collections import defaultdict
from datetime import datetime

import graphene
import pytz
from django.core.exceptions import ValidationError
from django.core.files import File
from django.db.models import F
from django.utils.text import slugify
from graphene.utils.str_converters import to_camel_case
from text_unidecode import unidecode

from ....core.http_client import HTTPClient
from ....core.tracing import traced_atomic_transaction
from ....core.utils import prepare_unique_slug
from ....core.utils.editorjs import clean_editor_js
from ....core.utils.validators import get_oembed_data
from ....discount.utils.promotion import mark_active_catalogue_promotion_rules_as_dirty
from ....permission.enums import ProductPermissions
from ....product import ProductMediaTypes, models
from ....product.error_codes import ProductBulkCreateErrorCode
from ....product.models import CollectionProduct
from ....thumbnail.utils import get_filename_from_url
from ....warehouse.models import Warehouse
from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.utils import get_webhooks_for_event
from ...attribute.types import AttributeValueInput
from ...attribute.utils import ProductAttributeAssignmentMixin
from ...channel import ChannelContext
from ...core.descriptions import ADDED_IN_313, PREVIEW_FEATURE, RICH_CONTENT
from ...core.doc_category import DOC_CATEGORY_PRODUCTS
from ...core.enums import ErrorPolicyEnum
from ...core.fields import JSONString
from ...core.mutations import BaseMutation, ModelMutation
from ...core.scalars import DateTime, WeightScalar
from ...core.types import (
    BaseInputObjectType,
    BaseObjectType,
    MediaInput,
    NonNullList,
    ProductBulkCreateError,
    SeoInput,
)
from ...core.utils import get_duplicated_values
from ...core.validators import clean_seo_fields
from ...core.validators.file import clean_image_file, is_image_url, validate_image_url
from ...meta.inputs import MetadataInput
from ...plugins.dataloaders import get_plugin_manager_promise
from ..mutations.product.product_create import ProductCreateInput
from ..types import Product
from ..utils import ALT_CHAR_LIMIT
from .product_variant_bulk_create import (
    ProductVariantBulkCreate,
    ProductVariantBulkCreateInput,
)


def get_results(instances_data_with_errors_list, reject_everything=False):
    if reject_everything:
        return [
            ProductBulkResult(product=None, errors=data.get("errors"))
            for data in instances_data_with_errors_list
        ]
    return [
        ProductBulkResult(
            product=ChannelContext(node=data.get("instance"), channel_slug=None),
            errors=data.get("errors"),
        )
        if data.get("instance")
        else ProductBulkResult(product=None, errors=data.get("errors"))
        for data in instances_data_with_errors_list
    ]


class ProductChannelListingCreateInput(BaseInputObjectType):
    channel_id = graphene.ID(required=True, description="ID of a channel.")
    is_published = graphene.Boolean(
        description="Determines if object is visible to customers."
    )
    published_at = DateTime(description="Publication date time. ISO 8601 standard.")
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
    available_for_purchase_at = DateTime(
        description=(
            "A start date time from which a product will be available "
            "for purchase. When not set and `isAvailable` is set to True, "
            "the current day is assumed."
        )
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductBulkResult(BaseObjectType):
    product = graphene.Field(Product, description="Product data.")
    errors = NonNullList(
        ProductBulkCreateError,
        required=False,
        description="List of errors occurred on create attempt.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductBulkCreateInput(ProductCreateInput):
    attributes = NonNullList(AttributeValueInput, description="List of attributes.")
    category = graphene.ID(description="ID of the product's category.", name="category")
    collections = NonNullList(
        graphene.ID,
        description="List of IDs of collections that the product belongs to.",
        name="collections",
    )
    description = JSONString(description="Product description." + RICH_CONTENT)
    name = graphene.String(description="Product name.")
    slug = graphene.String(description="Product slug.")
    tax_class = graphene.ID(
        description=(
            "ID of a tax class to assign to this product. If not provided, product "
            "will use the tax class which is assigned to the product type."
        ),
        required=False,
    )
    seo = SeoInput(description="Search engine optimization fields.")
    weight = WeightScalar(description="Weight of the Product.", required=False)
    rating = graphene.Float(description="Defines the product rating value.")
    metadata = NonNullList(
        MetadataInput,
        description="Fields required to update the product metadata.",
        required=False,
    )
    private_metadata = NonNullList(
        MetadataInput,
        description=("Fields required to update the product private metadata."),
        required=False,
    )
    external_reference = graphene.String(
        description="External ID of this product.", required=False
    )
    product_type = graphene.ID(
        description="ID of the type that product belongs to.",
        name="productType",
        required=True,
    )
    media = NonNullList(
        MediaInput,
        description="List of media inputs associated with the product.",
        required=False,
    )
    channel_listings = NonNullList(
        ProductChannelListingCreateInput,
        description="List of channels in which the product is available.",
        required=False,
    )
    variants = NonNullList(
        ProductVariantBulkCreateInput,
        required=False,
        description="Input list of product variants to create.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


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
            description="Policies of error handling. DEFAULT: "
            + ErrorPolicyEnum.REJECT_EVERYTHING.name,
        )

    class Meta:
        description = "Creates products." + ADDED_IN_313 + PREVIEW_FEATURE
        doc_category = DOC_CATEGORY_PRODUCTS
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductBulkCreateError
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def generate_unique_slug(cls, slugable_value, new_slugs):
        slug = slugify(unidecode(slugable_value))

        # in case when slugable_value contains only not allowed in slug characters,
        # slugify function will return empty string, so we need to provide some default
        # value
        if slug == "":
            slug = "-"

        search_field = "slug__iregex"
        pattern = rf"{slug}-\d+$|{slug}$"
        lookup = {search_field: pattern}

        slug_values = models.Product.objects.filter(**lookup).values_list(
            "slug", flat=True
        )
        slug_values = list(slug_values) + new_slugs
        unique_slug = prepare_unique_slug(slug, slug_values)
        new_slugs.append(unique_slug)

        return unique_slug

    @classmethod
    def clean_base_fields(
        cls, cleaned_input, new_slugs, product_index, index_error_map
    ):
        base_fields_errors_count = 0

        weight = cleaned_input.get("weight")
        if weight and weight.value < 0:
            index_error_map[product_index].append(
                ProductBulkCreateError(
                    path="weight",
                    message="Product can't have negative weight.",
                    code=ProductBulkCreateErrorCode.INVALID.value,
                )
            )
            base_fields_errors_count += 1

        description = cleaned_input.get("description")
        cleaned_input["description_plaintext"] = (
            clean_editor_js(description, to_string=True) if description else ""
        )

        slug = cleaned_input.get("slug")
        if not slug and "name" in cleaned_input:
            slug = cls.generate_unique_slug(cleaned_input["name"], new_slugs)
            cleaned_input["slug"] = slug

        clean_seo_fields(cleaned_input)

        return base_fields_errors_count

    @classmethod
    def add_indexes_to_errors(cls, index, error, index_error_map, path_prefix=None):
        for key, value in error.error_dict.items():
            for e in value:
                code = (
                    ProductBulkCreateErrorCode.INVALID.value
                    if e.code == ProductBulkCreateErrorCode.GRAPHQL_ERROR.value
                    else e.code
                )
                if path_prefix:
                    path = to_camel_case(f"{path_prefix}.{key}")
                else:
                    path = to_camel_case(key)
                index_error_map[index].append(
                    ProductBulkCreateError(
                        path=path,
                        message=e.messages[0],
                        code=code,
                    )
                )

    @classmethod
    def clean_attributes(cls, cleaned_input, product_index, index_error_map):
        attributes_errors_count = 0

        if attributes := cleaned_input.get("attributes"):
            try:
                attributes_qs = cleaned_input["product_type"].product_attributes.all()
                attributes = ProductAttributeAssignmentMixin.clean_input(
                    attributes, attributes_qs
                )
                cleaned_input["attributes"] = attributes
            except ValidationError as exc:
                if hasattr(exc, "error_dict"):
                    cls.add_indexes_to_errors(
                        product_index, exc, index_error_map, "attributes"
                    )
                else:
                    for error in exc.error_list:
                        index_error_map[product_index].append(
                            ProductBulkCreateError(
                                path="attributes",
                                message=error.message,
                                code=error.code,
                            )
                        )
                    attributes_errors_count += 1
        return attributes_errors_count

    @classmethod
    def _clean_channel_listing(
        cls, listings_data, channels_global_ids, product_index, index_error_map
    ):
        input_channel_ids = [
            channel_listing["channel_id"] for channel_listing in listings_data
        ]

        wrong_channel_ids = {
            channel_id
            for channel_id in input_channel_ids
            if channel_id not in channels_global_ids.keys()
        }
        if wrong_channel_ids:
            index_error_map[product_index].append(
                ProductBulkCreateError(
                    path="channelListings",
                    message="Not existing channel ID.",
                    code=ProductBulkCreateErrorCode.NOT_FOUND.value,
                    channels=wrong_channel_ids,
                )
            )

        duplicates = get_duplicated_values(input_channel_ids)
        if duplicates:
            index_error_map[product_index].append(
                ProductBulkCreateError(
                    path="channelListings",
                    message="Duplicated channel ID.",
                    code=ProductBulkCreateErrorCode.DUPLICATED_INPUT_ITEM.value,
                    channels=duplicates,
                )
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
        cls,
        listings_data,
        channel_global_id_to_instance_map,
        product_index,
        used_channels_map,
        index_error_map,
    ):
        listings_to_create = []

        duplicates, wrong_channel_ids = cls._clean_channel_listing(
            listings_data,
            channel_global_id_to_instance_map,
            product_index,
            index_error_map,
        )

        if not duplicates and not wrong_channel_ids:
            invalid_available_for_purchase = []

            for index, listing_data in enumerate(listings_data):
                is_available_for_purchase = listing_data.pop(
                    "is_available_for_purchase", None
                )
                available_for_purchase_at = listing_data.get(
                    "available_for_purchase_at"
                )

                if is_available_for_purchase is False and available_for_purchase_at:
                    invalid_available_for_purchase.append(listing_data["channel_id"])

                if invalid_available_for_purchase:
                    message = (
                        "Cannot set available for purchase at when"
                        " isAvailableForPurchase is false."
                    )
                    index_error_map[product_index].append(
                        ProductBulkCreateError(
                            path=f"channelListings.{index}",
                            message=message,
                            code=ProductBulkCreateErrorCode.NOT_FOUND.value,
                            channels=invalid_available_for_purchase,
                        )
                    )
                    continue

                channel = channel_global_id_to_instance_map[listing_data["channel_id"]]
                listing_data["channel"] = channel
                listing_data["currency"] = channel.currency_code
                cls.set_published_at(listing_data)

                if is_available_for_purchase is not None:
                    cls.set_available_for_purchase_at(
                        is_available_for_purchase,
                        available_for_purchase_at,
                        listing_data,
                    )
                used_channels_map[listing_data["channel_id"]] = channel
                listings_to_create.append(listing_data)
        return listings_to_create

    @classmethod
    def clean_media(cls, media_inputs, product_index, index_error_map):
        media_to_create = []

        for index, media_input in enumerate(media_inputs):
            image = media_input.get("image")
            media_url = media_input.get("media_url")
            alt = media_input.get("alt")

            if not image and not media_url:
                index_error_map[product_index].append(
                    ProductBulkCreateError(
                        path=f"media.{index}",
                        message="Image or external URL is required.",
                        code=ProductBulkCreateErrorCode.REQUIRED.value,
                    )
                )
                continue

            if image and media_url:
                index_error_map[product_index].append(
                    ProductBulkCreateError(
                        path=f"media.{index}",
                        message="Either image or external URL is required.",
                        code=ProductBulkCreateErrorCode.DUPLICATED_INPUT_ITEM.value,
                    )
                )
                continue

            if alt and len(alt) > ALT_CHAR_LIMIT:
                index_error_map[product_index].append(
                    ProductBulkCreateError(
                        path=f"media.{index}",
                        message=f"Alt field exceeds the character "
                        f"limit of {ALT_CHAR_LIMIT}.",
                        code=ProductBulkCreateErrorCode.INVALID.value,
                    )
                )
                continue
            media_to_create.append(media_input)

        return media_to_create

    @classmethod
    def clean_variants(
        cls,
        info,
        variant_inputs,
        product_channel_global_id_to_instance_map,
        warehouse_global_id_to_instance_map,
        duplicated_sku,
        product_type,
        product_index,
        index_error_map,
    ):
        variants_to_create: list = []
        variant_index_error_map: dict = defaultdict(list)

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

        for index, variant_data in enumerate(variant_inputs):
            variant_data["product_type"] = product_type
            cleaned_input = ProductVariantBulkCreate.clean_variant(
                info,
                variant_data,
                product_channel_global_id_to_instance_map,
                warehouse_global_id_to_instance_map,
                variant_attributes,
                [],
                variant_attributes_ids,
                variant_attributes_external_refs,
                duplicated_sku,
                variant_index_error_map,
                index,
                None,
            )
            variants_to_create.append(cleaned_input)

        for index, errors in variant_index_error_map.items():
            for error in errors:
                index_error_map[product_index].append(
                    ProductBulkCreateError(
                        path=f"variants.{index}.{error.path}"
                        if error.path
                        else f"variants.{index}",
                        message=error.message,
                        code=error.code,
                        attributes=error.attributes,
                        values=error.values,
                        warehouses=error.warehouses,
                        channels=error.channels,
                    )
                )
        return variants_to_create

    @classmethod
    def clean_product_input(
        cls,
        info,
        data: dict,
        channel_global_id_to_instance_map: dict,
        warehouse_global_id_to_instance_map: dict,
        duplicated_sku: set,
        new_slugs: list,
        product_index: int,
        index_error_map: dict,
    ):
        used_channels_map: dict = {}
        base_fields_errors_count = 0

        try:
            cleaned_input = ModelMutation.clean_input(
                info, None, data, input_cls=ProductBulkCreateInput
            )
        except ValidationError as exc:
            cls.add_indexes_to_errors(product_index, exc, index_error_map)
            return None

        base_fields_errors_count += cls.clean_base_fields(
            cleaned_input,
            new_slugs,
            product_index,
            index_error_map,
        )

        attributes_errors_count = cls.clean_attributes(
            cleaned_input, product_index, index_error_map
        )

        if media_inputs := cleaned_input.get("media"):
            cleaned_input["media"] = cls.clean_media(
                media_inputs, product_index, index_error_map
            )

        if listings_inputs := cleaned_input.get("channel_listings"):
            cleaned_input["channel_listings"] = cls.clean_product_channel_listings(
                listings_inputs,
                channel_global_id_to_instance_map,
                product_index,
                used_channels_map,
                index_error_map,
            )

        if variant_inputs := cleaned_input.get("variants"):
            cleaned_input["variants"] = cls.clean_variants(
                info,
                variant_inputs,
                used_channels_map,
                warehouse_global_id_to_instance_map,
                duplicated_sku,
                cleaned_input["product_type"],
                product_index,
                index_error_map,
            )

        if base_fields_errors_count > 0 or attributes_errors_count > 0:
            return None

        return cleaned_input if cleaned_input else None

    @classmethod
    def clean_products(cls, info, products_data, index_error_map):
        cleaned_inputs_map: dict = {}
        new_slugs: list = []

        warehouse_global_id_to_instance_map = {
            graphene.Node.to_global_id("Warehouse", warehouse.id): warehouse
            for warehouse in Warehouse.objects.all()
        }
        channel_global_id_to_instance_map = {
            graphene.Node.to_global_id("Channel", channel.id): channel
            for channel in models.Channel.objects.all()
        }

        duplicated_sku = get_duplicated_values(
            [
                variant.sku
                for product_data in products_data
                if product_data.variants
                for variant in product_data.variants
                if variant.sku
            ]
        )

        for product_index, product_data in enumerate(products_data):
            cleaned_input = cls.clean_product_input(
                info,
                product_data,
                channel_global_id_to_instance_map,
                warehouse_global_id_to_instance_map,
                duplicated_sku,
                new_slugs,
                product_index,
                index_error_map,
            )
            cleaned_inputs_map[product_index] = cleaned_input
        return cleaned_inputs_map

    @classmethod
    def create_products(cls, info, cleaned_inputs_map, index_error_map):
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

                instance = models.Product()
                instance = cls.construct_instance(instance, cleaned_input)
                cls.validate_and_update_metadata(
                    instance, metadata_list, private_metadata_list
                )
                cls.clean_instance(info, instance)
                instance.search_index_dirty = True

                instances_data_and_errors_list.append(
                    {
                        "instance": instance,
                        "errors": index_error_map[index],
                        "cleaned_input": cleaned_input,
                    }
                )
                # assign product instance to media data
                if media := cleaned_input.get("media"):
                    for media_input in media:
                        media_input["product"] = instance

                # assign product instance to variants data
                if variants := cleaned_input.get("variants"):
                    variants = cls.create_variants(
                        info, instance, variants, index, index_error_map
                    )
                    cleaned_input["variants"] = variants

                # assign product instance to channel listings data
                if channel_listings := cleaned_input.get("channel_listings"):
                    for channel_listing in channel_listings:
                        channel_listing["product"] = instance

            except ValidationError as exc:
                for key, value in exc.error_dict.items():
                    for e in value:
                        index_error_map[index].append(
                            ProductBulkCreateError(
                                path=to_camel_case(key),
                                message=e.messages[0],
                                code=e.code,
                            )
                        )
                instances_data_and_errors_list.append(
                    {"instance": None, "errors": index_error_map[index]}
                )

        return instances_data_and_errors_list

    @classmethod
    def create_variants(cls, info, product, variants_inputs, index, index_error_map):
        variants_instances_data = []

        for variant_index, variant_data in enumerate(variants_inputs):
            if variant_data:
                try:
                    metadata_list = variant_data.pop("metadata", None)
                    private_metadata_list = variant_data.pop("private_metadata", None)
                    variant = models.ProductVariant()
                    variant.product = product
                    variant = cls.construct_instance(variant, variant_data)
                    cls.validate_and_update_metadata(
                        variant, metadata_list, private_metadata_list
                    )
                    variant.full_clean(exclude=["product"])

                    # store variant related objects data to create related objects
                    # after variant instance will be created
                    variant_data = {
                        "instance": variant,
                        "cleaned_input": {
                            "attributes": variant_data.get("attributes"),
                            "channel_listings": variant_data.get("channel_listings"),
                            "stocks": variant_data.get("stocks"),
                        },
                    }
                    variants_instances_data.append(variant_data)
                except ValidationError as exc:
                    cls.add_indexes_to_errors(index, exc, index_error_map)

        return variants_instances_data

    @classmethod
    def save(cls, info, product_data_with_errors_list):
        products_to_create: list = []
        media_to_create: list = []
        attributes_to_save: list = []
        listings_to_create: list = []

        variants: list = []
        variants_input_data: list = []
        updated_channels: set = set()

        for product_data in product_data_with_errors_list:
            product = product_data["instance"]

            if not product:
                continue

            products_to_create.append(product)
            cleaned_input = product_data["cleaned_input"]

            if media_inputs := cleaned_input.get("media"):
                cls.prepare_media(info, product, media_inputs, media_to_create)

            if attributes := cleaned_input.get("attributes"):
                attributes_to_save.append((product, attributes))

            if listings_input := cleaned_input.get("channel_listings"):
                cls.prepare_products_channel_listings(
                    product,
                    listings_input,
                    listings_to_create,
                    updated_channels,
                )

            if variants_data := cleaned_input.pop("variants", None):
                variants_input_data.extend(variants_data)

        models.Product.objects.bulk_create(products_to_create)
        models.ProductMedia.objects.bulk_create(media_to_create)
        models.ProductChannelListing.objects.bulk_create(listings_to_create)

        for product, attributes in attributes_to_save:
            ProductAttributeAssignmentMixin.save(product, attributes)

        if variants_input_data:
            variants = cls.save_variants(info, variants_input_data)

        return variants, updated_channels

    @classmethod
    def _save_m2m(cls, _info, instances_data):
        product_collections = []
        for instance_data in instances_data:
            product = instance_data["instance"]
            if not product:
                continue

            cleaned_input = instance_data["cleaned_input"]
            if collections := cleaned_input.get("collections"):
                for collection in collections:
                    product_collections.append(
                        CollectionProduct(product=product, collection=collection)
                    )

        CollectionProduct.objects.bulk_create(product_collections)

    @classmethod
    def prepare_products_channel_listings(
        cls, product, listings_input, listings_to_create, updated_channels
    ):
        listings_to_create += [
            models.ProductChannelListing(
                product=product,
                channel=listing_data["channel"],
                currency=listing_data["channel"].currency_code,
                is_published=listing_data.get("is_published", False),
                published_at=listing_data.get("published_at"),
                visible_in_listings=listing_data.get("visible_in_listings", False),
                available_for_purchase_at=listing_data.get("available_for_purchase_at"),
            )
            for listing_data in listings_input
        ]
        updated_channels.update(
            {listing_data["channel"] for listing_data in listings_input}
        )

    @classmethod
    def save_variants(cls, info, variants_input_data):
        return ProductVariantBulkCreate.save_variants(info, variants_input_data, None)

    @classmethod
    def prepare_media(cls, info, product, media_inputs, media_to_create):
        for media_input in media_inputs:
            alt = media_input.get("alt", "")
            media_url = media_input.get("media_url")
            if img_data := media_input.get("image"):
                media_input["image"] = info.context.FILES.get(img_data)
                image_data = clean_image_file(
                    media_input, "image", ProductBulkCreateErrorCode
                )
                media_to_create.append(
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
                        media_url, "media_url", ProductBulkCreateErrorCode.INVALID.value
                    )
                    filename = get_filename_from_url(media_url)
                    image_data = HTTPClient.send_request(
                        "GET", media_url, stream=True, timeout=30, allow_redirects=False
                    )
                    image_data = File(image_data.raw, filename)
                    media_to_create.append(
                        models.ProductMedia(
                            image=image_data,
                            alt=alt,
                            product=product,
                            type=ProductMediaTypes.IMAGE,
                        )
                    )
                else:
                    oembed_data, media_type = get_oembed_data(media_url, "media_url")
                    media_to_create.append(
                        models.ProductMedia(
                            external_url=oembed_data["url"],
                            alt=oembed_data.get("title", alt),
                            product=product,
                            type=media_type,
                            oembed_data=oembed_data,
                        )
                    )

    @classmethod
    def post_save_actions(cls, info, products, variants, channels):
        manager = get_plugin_manager_promise(info.context).get()
        product_ids = []
        webhooks = get_webhooks_for_event(WebhookEventAsyncType.PRODUCT_CREATED)
        for product in products:
            cls.call_event(manager.product_created, product.node, webhooks=webhooks)
            product_ids.append(product.node.id)

        webhooks = get_webhooks_for_event(WebhookEventAsyncType.PRODUCT_VARIANT_CREATED)
        for variant in variants:
            cls.call_event(manager.product_variant_created, variant, webhooks=webhooks)

        if products:
            channel_ids = set([channel.id for channel in channels])
            cls.call_event(mark_active_catalogue_promotion_rules_as_dirty, channel_ids)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, root, info, **data):
        index_error_map: dict = defaultdict(list)
        error_policy = data.get("error_policy", ErrorPolicyEnum.REJECT_EVERYTHING.value)

        # clean and validate inputs
        cleaned_inputs_map = cls.clean_products(info, data["products"], index_error_map)
        instances_data_with_errors_list = cls.create_products(
            info, cleaned_inputs_map, index_error_map
        )

        # check error policy
        if any([True if error else False for error in index_error_map.values()]):
            if error_policy == ErrorPolicyEnum.REJECT_EVERYTHING.value:
                results = get_results(instances_data_with_errors_list, True)
                return ProductBulkCreate(count=0, results=results)

            if error_policy == ErrorPolicyEnum.REJECT_FAILED_ROWS.value:
                for data in instances_data_with_errors_list:
                    if data["errors"] and data["instance"]:
                        data["instance"] = None

        # save all objects
        variants, updated_channels = cls.save(info, instances_data_with_errors_list)

        # save m2m fields
        cls._save_m2m(info, instances_data_with_errors_list)

        # prepare and return data
        results = get_results(instances_data_with_errors_list)
        products = [result.product for result in results if result.product]

        cls.post_save_actions(info, products, variants, updated_channels)

        return ProductBulkCreate(count=len(products), results=results)
