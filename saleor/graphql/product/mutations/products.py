import datetime
from collections import defaultdict
from typing import List, Tuple

import graphene
import pytz
import requests
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.files import File
from django.db import transaction
from django.db.models import Exists, OuterRef
from django.utils.text import slugify

from ....attribute import AttributeInputType
from ....attribute import models as attribute_models
from ....core.exceptions import PreorderAllocationError
from ....core.permissions import ProductPermissions
from ....core.tracing import traced_atomic_transaction
from ....core.utils.date_time import convert_to_utc_date_time
from ....core.utils.editorjs import clean_editor_js
from ....core.utils.validators import get_oembed_data
from ....order import events as order_events
from ....order import models as order_models
from ....order.tasks import recalculate_orders_task
from ....product import ProductMediaTypes, models
from ....product.error_codes import CollectionErrorCode, ProductErrorCode
from ....product.search import update_product_search_vector
from ....product.tasks import (
    update_product_discounted_price_task,
    update_products_discounted_prices_of_catalogues_task,
)
from ....product.utils import delete_categories, get_products_ids_without_variants
from ....product.utils.variants import generate_and_set_variant_name
from ....thumbnail import models as thumbnail_models
from ....warehouse.management import deactivate_preorder_for_variant
from ...attribute.types import AttributeValueInput
from ...attribute.utils import AttributeAssignmentMixin, AttrValuesInput
from ...channel import ChannelContext
from ...core.descriptions import (
    ADDED_IN_31,
    DEPRECATED_IN_3X_INPUT,
    PREVIEW_FEATURE,
    RICH_CONTENT,
)
from ...core.fields import JSONString
from ...core.inputs import ReorderInput
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.scalars import WeightScalar
from ...core.types import CollectionError, NonNullList, ProductError, SeoInput, Upload
from ...core.utils import (
    add_hash_to_file_name,
    clean_seo_fields,
    get_duplicated_values,
    get_filename_from_url,
    is_image_url,
    validate_image_file,
    validate_image_url,
    validate_slug_and_generate_if_needed,
)
from ...core.utils.reordering import perform_reordering
from ...warehouse.types import Warehouse
from ..types import Category, Collection, Product, ProductMedia, ProductVariant
from ..utils import (
    clean_variant_sku,
    create_stocks,
    get_draft_order_lines_data_for_variants,
    get_used_attribute_values_for_variant,
    get_used_variants_attribute_values,
    update_ordered_media,
)


class CategoryInput(graphene.InputObjectType):
    description = JSONString(description="Category description." + RICH_CONTENT)
    name = graphene.String(description="Category name.")
    slug = graphene.String(description="Category slug.")
    seo = SeoInput(description="Search engine optimization fields.")
    background_image = Upload(description="Background image file.")
    background_image_alt = graphene.String(description="Alt text for a product media.")


class CategoryCreate(ModelMutation):
    class Arguments:
        input = CategoryInput(
            required=True, description="Fields required to create a category."
        )
        parent_id = graphene.ID(
            description=(
                "ID of the parent category. If empty, category will be top level "
                "category."
            ),
            name="parent",
        )

    class Meta:
        description = "Creates a new category."
        model = models.Category
        object_type = Category
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        description = cleaned_input.get("description")
        cleaned_input["description_plaintext"] = (
            clean_editor_js(description, to_string=True) if description else ""
        )
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = ProductErrorCode.REQUIRED.value
            raise ValidationError({"slug": error})
        parent_id = data["parent_id"]
        if parent_id:
            parent = cls.get_node_or_error(
                info, parent_id, field="parent", only_type=Category
            )
            cleaned_input["parent"] = parent
        if data.get("background_image"):
            image_data = info.context.FILES.get(data["background_image"])
            validate_image_file(image_data, "background_image", ProductErrorCode)
            add_hash_to_file_name(image_data)
        clean_seo_fields(cleaned_input)
        return cleaned_input

    @classmethod
    def perform_mutation(cls, root, info, **data):
        parent_id = data.pop("parent_id", None)
        data["input"]["parent_id"] = parent_id
        return super().perform_mutation(root, info, **data)

    @classmethod
    def post_save_action(cls, info, instance, _cleaned_input):
        info.context.plugins.category_created(instance)


class CategoryUpdate(CategoryCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a category to update.")
        input = CategoryInput(
            required=True, description="Fields required to update a category."
        )

    class Meta:
        description = "Updates a category."
        model = models.Category
        object_type = Category
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        # delete old background image and related thumbnails
        if "background_image" in cleaned_data and instance.background_image:
            instance.background_image.delete()
            thumbnail_models.Thumbnail.objects.filter(category_id=instance.id).delete()
        return super().construct_instance(instance, cleaned_data)

    @classmethod
    def post_save_action(cls, info, instance, _cleaned_input):
        info.context.plugins.category_updated(instance)


class CategoryDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a category to delete.")

    class Meta:
        description = "Deletes a category."
        model = models.Category
        object_type = Category
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")
        instance = cls.get_node_or_error(info, node_id, only_type=Category)

        db_id = instance.id

        delete_categories([db_id], manager=info.context.plugins)

        instance.id = db_id
        return cls.success_response(instance)


class CollectionInput(graphene.InputObjectType):
    is_published = graphene.Boolean(
        description="Informs whether a collection is published."
    )
    name = graphene.String(description="Name of the collection.")
    slug = graphene.String(description="Slug of the collection.")
    description = JSONString(
        description="Description of the collection." + RICH_CONTENT
    )
    background_image = Upload(description="Background image file.")
    background_image_alt = graphene.String(description="Alt text for an image.")
    seo = SeoInput(description="Search engine optimization fields.")
    publication_date = graphene.Date(
        description=(f"Publication date. ISO 8601 standard. {DEPRECATED_IN_3X_INPUT}")
    )


class CollectionCreateInput(CollectionInput):
    products = NonNullList(
        graphene.ID,
        description="List of products to be added to the collection.",
        name="products",
    )


class CollectionCreate(ModelMutation):
    class Arguments:
        input = CollectionCreateInput(
            required=True, description="Fields required to create a collection."
        )

    class Meta:
        description = "Creates a new collection."
        model = models.Collection
        object_type = Collection
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = CollectionErrorCode.REQUIRED.value
            raise ValidationError({"slug": error})
        if data.get("background_image"):
            image_data = info.context.FILES.get(data["background_image"])
            validate_image_file(image_data, "background_image", CollectionErrorCode)
            add_hash_to_file_name(image_data)
        is_published = cleaned_input.get("is_published")
        publication_date = cleaned_input.get("publication_date")
        if is_published and not publication_date:
            cleaned_input["published_at"] = datetime.datetime.now(pytz.UTC)
        elif publication_date:
            cleaned_input["published_at"] = convert_to_utc_date_time(publication_date)
        clean_seo_fields(cleaned_input)
        return cleaned_input

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        info.context.plugins.collection_created(instance)

        products = instance.products.prefetched_for_webhook(single_object=False)
        for product in products:
            info.context.plugins.product_updated(product)

    @classmethod
    def perform_mutation(cls, _root, info, **kwargs):
        result = super().perform_mutation(_root, info, **kwargs)
        return CollectionCreate(
            collection=ChannelContext(node=result.collection, channel_slug=None)
        )


class CollectionUpdate(CollectionCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a collection to update.")
        input = CollectionInput(
            required=True, description="Fields required to update a collection."
        )

    class Meta:
        description = "Updates a collection."
        model = models.Collection
        object_type = Collection
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    def construct_instance(cls, instance, cleaned_data):
        # delete old background image and related thumbnails
        if "background_image" in cleaned_data and instance.background_image:
            instance.background_image.delete()
            thumbnail_models.Thumbnail.objects.filter(
                collection_id=instance.id
            ).delete()
        return super().construct_instance(instance, cleaned_data)

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        """Override this method with `pass` to avoid triggering product webhook."""
        info.context.plugins.collection_updated(instance)


class CollectionDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a collection to delete.")

    class Meta:
        description = "Deletes a collection."
        model = models.Collection
        object_type = Collection
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **kwargs):
        node_id = kwargs.get("id")

        instance = cls.get_node_or_error(info, node_id, only_type=Collection)
        products = list(instance.products.prefetched_for_webhook(single_object=False))

        result = super().perform_mutation(_root, info, **kwargs)

        info.context.plugins.collection_deleted(instance)
        for product in products:
            info.context.plugins.product_updated(product)

        return CollectionDelete(
            collection=ChannelContext(node=result.collection, channel_slug=None)
        )


class MoveProductInput(graphene.InputObjectType):
    product_id = graphene.ID(
        description="The ID of the product to move.", required=True
    )
    sort_order = graphene.Int(
        description=(
            "The relative sorting position of the product (from -inf to +inf) "
            "starting from the first given product's actual position."
            "1 moves the item one position forward, -1 moves the item one position "
            "backward, 0 leaves the item unchanged."
        )
    )


class CollectionReorderProducts(BaseMutation):
    collection = graphene.Field(
        Collection, description="Collection from which products are reordered."
    )

    class Meta:
        description = "Reorder the products of a collection."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    class Arguments:
        collection_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a collection."
        )
        moves = NonNullList(
            MoveProductInput,
            required=True,
            description="The collection products position operations.",
        )

    @classmethod
    def perform_mutation(cls, _root, info, collection_id, moves):
        pk = cls.get_global_id_or_error(
            collection_id, only_type=Collection, field="collection_id"
        )

        try:
            collection = models.Collection.objects.prefetch_related(
                "collectionproduct"
            ).get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "collection_id": ValidationError(
                        f"Couldn't resolve to a collection: {collection_id}",
                        code=ProductErrorCode.NOT_FOUND,
                    )
                }
            )

        m2m_related_field = collection.collectionproduct

        operations = {}

        # Resolve the products
        for move_info in moves:
            product_pk = cls.get_global_id_or_error(
                move_info.product_id, only_type=Product, field="moves"
            )

            try:
                m2m_info = m2m_related_field.get(product_id=int(product_pk))
            except ObjectDoesNotExist:
                raise ValidationError(
                    {
                        "moves": ValidationError(
                            f"Couldn't resolve to a product: {move_info.product_id}",
                            code=CollectionErrorCode.NOT_FOUND.value,
                        )
                    }
                )
            operations[m2m_info.pk] = move_info.sort_order

        with traced_atomic_transaction():
            perform_reordering(m2m_related_field, operations)
        collection = ChannelContext(node=collection, channel_slug=None)
        return CollectionReorderProducts(collection=collection)


class CollectionAddProducts(BaseMutation):
    collection = graphene.Field(
        Collection, description="Collection to which products will be added."
    )

    class Arguments:
        collection_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a collection."
        )
        products = NonNullList(
            graphene.ID, required=True, description="List of product IDs."
        )

    class Meta:
        description = "Adds products to a collection."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, collection_id, products):
        collection = cls.get_node_or_error(
            info, collection_id, field="collection_id", only_type=Collection
        )
        products = cls.get_nodes_or_error(
            products,
            "products",
            Product,
            qs=models.Product.objects.prefetched_for_webhook(single_object=False),
        )
        cls.clean_products(products)
        collection.products.add(*products)
        if collection.sale_set.exists():
            # Updated the db entries, recalculating discounts of affected products
            update_products_discounted_prices_of_catalogues_task.delay(
                product_ids=[pq.pk for pq in products]
            )
        transaction.on_commit(
            lambda: [
                info.context.plugins.product_updated(product) for product in products
            ]
        )
        return CollectionAddProducts(
            collection=ChannelContext(node=collection, channel_slug=None)
        )

    @classmethod
    def clean_products(cls, products):
        products_ids_without_variants = get_products_ids_without_variants(products)
        if products_ids_without_variants:
            code = CollectionErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.value
            raise ValidationError(
                {
                    "products": ValidationError(
                        "Cannot manage products without variants.",
                        code=code,
                        params={"products": products_ids_without_variants},
                    )
                }
            )


class CollectionRemoveProducts(BaseMutation):
    collection = graphene.Field(
        Collection, description="Collection from which products will be removed."
    )

    class Arguments:
        collection_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a collection."
        )
        products = NonNullList(
            graphene.ID, required=True, description="List of product IDs."
        )

    class Meta:
        description = "Remove products from a collection."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    def perform_mutation(cls, _root, info, collection_id, products):
        collection = cls.get_node_or_error(
            info, collection_id, field="collection_id", only_type=Collection
        )
        products = cls.get_nodes_or_error(
            products,
            "products",
            only_type=Product,
            qs=models.Product.objects.prefetched_for_webhook(single_object=False),
        )
        collection.products.remove(*products)
        for product in products:
            info.context.plugins.product_updated(product)
        if collection.sale_set.exists():
            # Updated the db entries, recalculating discounts of affected products
            update_products_discounted_prices_of_catalogues_task.delay(
                product_ids=[p.pk for p in products]
            )
        return CollectionRemoveProducts(
            collection=ChannelContext(node=collection, channel_slug=None)
        )


class ProductInput(graphene.InputObjectType):
    attributes = NonNullList(AttributeValueInput, description="List of attributes.")
    category = graphene.ID(description="ID of the product's category.", name="category")
    charge_taxes = graphene.Boolean(
        description="Determine if taxes are being charged for the product."
    )
    collections = NonNullList(
        graphene.ID,
        description="List of IDs of collections that the product belongs to.",
        name="collections",
    )
    description = JSONString(description="Product description." + RICH_CONTENT)
    name = graphene.String(description="Product name.")
    slug = graphene.String(description="Product slug.")
    tax_code = graphene.String(description="Tax rate for enabled tax gateway.")
    seo = SeoInput(description="Search engine optimization fields.")
    weight = WeightScalar(description="Weight of the Product.", required=False)
    rating = graphene.Float(description="Defines the product rating value.")


class StockInput(graphene.InputObjectType):
    warehouse = graphene.ID(
        required=True, description="Warehouse in which stock is located."
    )
    quantity = graphene.Int(
        required=True, description="Quantity of items available for sell."
    )


class ProductCreateInput(ProductInput):
    product_type = graphene.ID(
        description="ID of the type that product belongs to.",
        name="productType",
        required=True,
    )


T_INPUT_MAP = List[Tuple[attribute_models.Attribute, AttrValuesInput]]


class ProductCreate(ModelMutation):
    class Arguments:
        input = ProductCreateInput(
            required=True, description="Fields required to create a product."
        )

    class Meta:
        description = "Creates a new product."
        model = models.Product
        object_type = Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def clean_attributes(
        cls, attributes: dict, product_type: models.ProductType
    ) -> T_INPUT_MAP:
        attributes_qs = product_type.product_attributes
        attributes = AttributeAssignmentMixin.clean_input(attributes, attributes_qs)
        return attributes

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)

        description = cleaned_input.get("description")
        cleaned_input["description_plaintext"] = (
            clean_editor_js(description, to_string=True) if description else ""
        )

        weight = cleaned_input.get("weight")
        if weight and weight.value < 0:
            raise ValidationError(
                {
                    "weight": ValidationError(
                        "Product can't have negative weight.",
                        code=ProductErrorCode.INVALID.value,
                    )
                }
            )

        # Attributes are provided as list of `AttributeValueInput` objects.
        # We need to transform them into the format they're stored in the
        # `Product` model, which is HStore field that maps attribute's PK to
        # the value's PK.

        attributes = cleaned_input.get("attributes")
        product_type = (
            instance.product_type if instance.pk else cleaned_input.get("product_type")
        )  # type: models.ProductType

        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = ProductErrorCode.REQUIRED.value
            raise ValidationError({"slug": error})

        if "tax_code" in cleaned_input:
            info.context.plugins.assign_tax_code_to_object_meta(
                instance, cleaned_input["tax_code"]
            )

        if attributes and product_type:
            try:
                cleaned_input["attributes"] = cls.clean_attributes(
                    attributes, product_type
                )
            except ValidationError as exc:
                raise ValidationError({"attributes": exc})

        clean_seo_fields(cleaned_input)
        return cleaned_input

    @classmethod
    def get_instance(cls, info, **data):
        """Prefetch related fields that are needed to process the mutation."""
        # If we are updating an instance and want to update its attributes,
        # prefetch them.

        object_id = data.get("id")
        if object_id and data.get("attributes"):
            # Prefetches needed by AttributeAssignmentMixin and
            # associate_attribute_values_to_instance
            qs = cls.Meta.model.objects.prefetch_related(
                "product_type__product_attributes__values",
                "product_type__attributeproduct",
            )
            return cls.get_node_or_error(info, object_id, only_type="Product", qs=qs)

        return super().get_instance(info, **data)

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info, instance, cleaned_input):
        instance.save()
        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        collections = cleaned_data.get("collections", None)
        if collections is not None:
            instance.collections.set(collections)

    @classmethod
    def post_save_action(cls, info, instance, _cleaned_input):
        product = models.Product.objects.prefetched_for_webhook().get(pk=instance.pk)
        update_product_search_vector(instance)
        info.context.plugins.product_created(product)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        product = getattr(response, cls._meta.return_field_name)

        # Wrap product instance with ChannelContext in response
        setattr(
            response,
            cls._meta.return_field_name,
            ChannelContext(node=product, channel_slug=None),
        )
        return response


class ProductUpdate(ProductCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product to update.")
        input = ProductInput(
            required=True, description="Fields required to update a product."
        )

    class Meta:
        description = "Updates an existing product."
        model = models.Product
        object_type = Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def clean_attributes(
        cls, attributes: dict, product_type: models.ProductType
    ) -> T_INPUT_MAP:
        attributes_qs = product_type.product_attributes
        attributes = AttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, creation=False
        )
        return attributes

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info, instance, cleaned_input):
        instance.save()
        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)

    @classmethod
    def post_save_action(cls, info, instance, _cleaned_input):
        product = models.Product.objects.prefetched_for_webhook().get(pk=instance.pk)
        update_product_search_vector(instance)
        info.context.plugins.product_updated(product)


class ProductDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product to delete.")

    class Meta:
        description = "Deletes a product."
        model = models.Product
        object_type = Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")

        instance = cls.get_node_or_error(info, node_id, only_type=Product)
        variants_id = list(instance.variants.all().values_list("id", flat=True))

        cls.delete_assigned_attribute_values(instance)

        draft_order_lines_data = get_draft_order_lines_data_for_variants(variants_id)

        response = super().perform_mutation(_root, info, **data)

        # delete order lines for deleted variant
        order_models.OrderLine.objects.filter(
            pk__in=draft_order_lines_data.line_pks
        ).delete()

        # run order event for deleted lines
        for order, order_lines in draft_order_lines_data.order_to_lines_mapping.items():
            order_events.order_line_product_removed_event(
                order, info.context.user, info.context.app, order_lines
            )

        order_pks = draft_order_lines_data.order_pks
        if order_pks:
            recalculate_orders_task.delay(list(order_pks))
        transaction.on_commit(
            lambda: info.context.plugins.product_deleted(instance, variants_id)
        )

        return response

    @staticmethod
    def delete_assigned_attribute_values(instance):
        attribute_models.AttributeValue.objects.filter(
            productassignments__product_id=instance.id,
            attribute__input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES,
        ).delete()


class PreorderSettingsInput(graphene.InputObjectType):
    global_threshold = graphene.Int(
        description="The global threshold for preorder variant."
    )
    end_date = graphene.DateTime(description="The end date for preorder.")


class ProductVariantInput(graphene.InputObjectType):
    attributes = NonNullList(
        AttributeValueInput,
        required=False,
        description="List of attributes specific to this variant.",
    )
    sku = graphene.String(description="Stock keeping unit.")
    track_inventory = graphene.Boolean(
        description=(
            "Determines if the inventory of this variant should be tracked. If false, "
            "the quantity won't change when customers buy this item."
        )
    )
    weight = WeightScalar(description="Weight of the Product Variant.", required=False)
    preorder = PreorderSettingsInput(
        description=(
            "Determines if variant is in preorder." + ADDED_IN_31 + PREVIEW_FEATURE
        )
    )
    quantity_limit_per_customer = graphene.Int(
        required=False,
        description=(
            "Determines maximum quantity of `ProductVariant`,"
            "that can be bought in a single checkout." + ADDED_IN_31 + PREVIEW_FEATURE
        ),
    )


class ProductVariantCreateInput(ProductVariantInput):
    attributes = NonNullList(
        AttributeValueInput,
        required=True,
        description="List of attributes specific to this variant.",
    )
    product = graphene.ID(
        description="Product ID of which type is the variant.",
        name="product",
        required=True,
    )
    stocks = NonNullList(
        StockInput,
        description="Stocks of a product available for sale.",
        required=False,
    )


class ProductVariantCreate(ModelMutation):
    class Arguments:
        input = ProductVariantCreateInput(
            required=True, description="Fields required to create a product variant."
        )

    class Meta:
        description = "Creates a new variant for a product."
        model = models.ProductVariant
        object_type = ProductVariant
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
        errors_mapping = {"price_amount": "price"}

    @classmethod
    def clean_attributes(
        cls, attributes: dict, product_type: models.ProductType
    ) -> T_INPUT_MAP:
        attributes_qs = product_type.variant_attributes
        attributes = AttributeAssignmentMixin.clean_input(attributes, attributes_qs)
        return attributes

    @classmethod
    def validate_duplicated_attribute_values(
        cls, attributes_data, used_attribute_values, instance=None
    ):
        attribute_values = defaultdict(list)
        for attr, attr_data in attributes_data:
            if attr.input_type == AttributeInputType.FILE:
                values = (
                    [slugify(attr_data.file_url.split("/")[-1])]
                    if attr_data.file_url
                    else []
                )
            else:
                values = attr_data.values
            attribute_values[attr_data.global_id].extend(values)
        if attribute_values in used_attribute_values:
            raise ValidationError(
                "Duplicated attribute values for product variant.",
                code=ProductErrorCode.DUPLICATED_INPUT_ITEM.value,
                params={"attributes": attribute_values.keys()},
            )
        else:
            used_attribute_values.append(attribute_values)

    @classmethod
    def clean_input(
        cls, info, instance: models.ProductVariant, data: dict, input_cls=None
    ):
        cleaned_input = super().clean_input(info, instance, data)

        weight = cleaned_input.get("weight")
        if weight and weight.value < 0:
            raise ValidationError(
                {
                    "weight": ValidationError(
                        "Product variant can't have negative weight.",
                        code=ProductErrorCode.INVALID.value,
                    )
                }
            )

        quantity_limit_per_customer = cleaned_input.get("quantity_limit_per_customer")
        if quantity_limit_per_customer is not None and quantity_limit_per_customer < 1:
            raise ValidationError(
                {
                    "quantity_limit_per_customer": ValidationError(
                        (
                            "Product variant can't have "
                            "quantity_limit_per_customer lower than 1."
                        ),
                        code=ProductErrorCode.INVALID.value,
                    )
                }
            )

        stocks = cleaned_input.get("stocks")
        if stocks:
            cls.check_for_duplicates_in_stocks(stocks)

        if instance.pk:
            # If the variant is getting updated,
            # simply retrieve the associated product type
            product_type = instance.product.product_type
            used_attribute_values = get_used_variants_attribute_values(instance.product)
        else:
            # If the variant is getting created, no product type is associated yet,
            # retrieve it from the required "product" input field
            product_type = cleaned_input["product"].product_type
            used_attribute_values = get_used_variants_attribute_values(
                cleaned_input["product"]
            )

        variant_attributes_ids = {
            graphene.Node.to_global_id("Attribute", attr_id)
            for attr_id in list(
                product_type.variant_attributes.all().values_list("pk", flat=True)
            )
        }
        attributes = cleaned_input.get("attributes")
        attributes_ids = {attr["id"] for attr in attributes or []}
        invalid_attributes = attributes_ids - variant_attributes_ids
        if len(invalid_attributes) > 0:
            raise ValidationError(
                "Given attributes are not a variant attributes.",
                code=ProductErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED.value,
                params={"attributes": invalid_attributes},
            )

        # Run the validation only if product type is configurable
        if product_type.has_variants:
            # Attributes are provided as list of `AttributeValueInput` objects.
            # We need to transform them into the format they're stored in the
            # `Product` model, which is HStore field that maps attribute's PK to
            # the value's PK.
            try:
                if attributes:
                    cleaned_attributes = cls.clean_attributes(attributes, product_type)
                    cls.validate_duplicated_attribute_values(
                        cleaned_attributes, used_attribute_values, instance
                    )
                    cleaned_input["attributes"] = cleaned_attributes
                # elif not instance.pk and not attributes:
                elif not instance.pk and (
                    not attributes
                    and product_type.variant_attributes.filter(value_required=True)
                ):
                    # if attributes were not provided on creation
                    raise ValidationError(
                        "All required attributes must take a value.",
                        ProductErrorCode.REQUIRED.value,
                    )
            except ValidationError as exc:
                raise ValidationError({"attributes": exc})
        else:
            if attributes:
                raise ValidationError(
                    "Cannot assign attributes for product type without variants",
                    ProductErrorCode.INVALID.value,
                )

        if "sku" in cleaned_input:
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
    def check_for_duplicates_in_stocks(cls, stocks_data):
        warehouse_ids = [stock["warehouse"] for stock in stocks_data]
        duplicates = get_duplicated_values(warehouse_ids)
        if duplicates:
            error_msg = "Duplicated warehouse ID: {}".format(", ".join(duplicates))
            raise ValidationError(
                {
                    "stocks": ValidationError(
                        error_msg, code=ProductErrorCode.UNIQUE.value
                    )
                }
            )

    @classmethod
    def get_instance(cls, info, **data):
        """Prefetch related fields that are needed to process the mutation.

        If we are updating an instance and want to update its attributes,
        # prefetch them.
        """

        object_id = data.get("id")
        if object_id and data.get("attributes"):
            # Prefetches needed by AttributeAssignmentMixin and
            # associate_attribute_values_to_instance
            qs = cls.Meta.model.objects.prefetch_related(
                "product__product_type__variant_attributes__values",
                "product__product_type__attributevariant",
            )
            return cls.get_node_or_error(
                info, object_id, only_type="ProductVariant", qs=qs
            )

        return super().get_instance(info, **data)

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info, instance, cleaned_input):
        new_variant = instance.pk is None
        instance.save()
        if not instance.product.default_variant:
            instance.product.default_variant = instance
            instance.product.save(update_fields=["default_variant", "updated_at"])
        # Recalculate the "discounted price" for the parent product
        update_product_discounted_price_task.delay(instance.product_id)
        stocks = cleaned_input.get("stocks")
        if stocks:
            cls.create_variant_stocks(instance, stocks)

        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)

        generate_and_set_variant_name(instance, cleaned_input.get("sku"))
        update_product_search_vector(instance.product)
        event_to_call = (
            info.context.plugins.product_variant_created
            if new_variant
            else info.context.plugins.product_variant_updated
        )
        transaction.on_commit(lambda: event_to_call(instance))

    @classmethod
    def create_variant_stocks(cls, variant, stocks):
        warehouse_ids = [stock["warehouse"] for stock in stocks]
        warehouses = cls.get_nodes_or_error(
            warehouse_ids, "warehouse", only_type=Warehouse
        )
        create_stocks(variant, stocks, warehouses)

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)


class ProductVariantUpdate(ProductVariantCreate):
    class Arguments:
        id = graphene.ID(
            required=True, description="ID of a product variant to update."
        )
        input = ProductVariantInput(
            required=True, description="Fields required to update a product variant."
        )

    class Meta:
        description = "Updates an existing variant for product."
        model = models.ProductVariant
        object_type = ProductVariant
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
        errors_mapping = {"price_amount": "price"}

    @classmethod
    def clean_attributes(
        cls, attributes: dict, product_type: models.ProductType
    ) -> T_INPUT_MAP:
        attributes_qs = product_type.variant_attributes
        attributes = AttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, creation=False
        )
        return attributes

    @classmethod
    def validate_duplicated_attribute_values(
        cls, attributes_data, used_attribute_values, instance=None
    ):
        # Check if the variant is getting updated,
        # and the assigned attributes do not change
        if instance.product_id is not None:
            assigned_attributes = get_used_attribute_values_for_variant(instance)
            input_attribute_values = defaultdict(list)
            for attr, attr_data in attributes_data:
                if attr.input_type == AttributeInputType.FILE:
                    values = (
                        [slugify(attr_data.file_url.split("/")[-1])]
                        if attr_data.file_url
                        else []
                    )
                else:
                    values = attr_data.values
                input_attribute_values[attr_data.global_id].extend(values)
            if input_attribute_values == assigned_attributes:
                return
        # if assigned attributes is getting updated run duplicated attribute validation
        super().validate_duplicated_attribute_values(
            attributes_data, used_attribute_values
        )


class ProductVariantDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description="ID of a product variant to delete."
        )

    class Meta:
        description = "Deletes a product variant."
        model = models.ProductVariant
        object_type = ProductVariant
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def success_response(cls, instance):
        # Update the "discounted_prices" of the parent product
        update_product_discounted_price_task.delay(instance.product_id)
        product = models.Product.objects.get(id=instance.product_id)
        update_product_search_vector(product)
        # if the product default variant has been removed set the new one
        if not product.default_variant:
            product.default_variant = product.variants.first()
            product.save(update_fields=["default_variant", "updated_at"])
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")
        instance = cls.get_node_or_error(info, node_id, only_type=ProductVariant)

        draft_order_lines_data = get_draft_order_lines_data_for_variants([instance.pk])

        # Get cached variant with related fields to fully populate webhook payload.
        variant = (
            models.ProductVariant.objects.prefetch_related(
                "channel_listings", "attributes__values", "variant_media"
            )
        ).get(id=instance.id)

        cls.delete_assigned_attribute_values(variant)
        cls.delete_product_channel_listings_without_available_variants(variant)
        response = super().perform_mutation(_root, info, **data)

        # delete order lines for deleted variant
        order_models.OrderLine.objects.filter(
            pk__in=draft_order_lines_data.line_pks
        ).delete()

        # run order event for deleted lines
        for order, order_lines in draft_order_lines_data.order_to_lines_mapping.items():
            order_events.order_line_variant_removed_event(
                order, info.context.user, info.context.app, order_lines
            )

        order_pks = draft_order_lines_data.order_pks
        if order_pks:
            recalculate_orders_task.delay(list(order_pks))

        transaction.on_commit(
            lambda: info.context.plugins.product_variant_deleted(variant)
        )

        return response

    @staticmethod
    def delete_assigned_attribute_values(instance):
        attribute_models.AttributeValue.objects.filter(
            variantassignments__variant_id=instance.id,
            attribute__input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES,
        ).delete()

    @staticmethod
    def delete_product_channel_listings_without_available_variants(instance):
        """Delete invalid product channel listings.

        Delete product channel listings for channels for which the deleted variant
        was the last available variant.
        """
        channel_ids = set(
            instance.channel_listings.values_list("channel_id", flat=True)
        )
        product_id = instance.product_id
        variants = (
            models.ProductVariant.objects.filter(product_id=product_id)
            .exclude(id=instance.id)
            .values("id")
        )
        available_channel_ids = set(
            models.ProductVariantChannelListing.objects.filter(
                Exists(
                    variants.filter(id=OuterRef("variant_id")),
                    channel_id__in=channel_ids,
                )
            ).values_list("channel_id", flat=True)
        )
        not_available_channel_ids = channel_ids - available_channel_ids
        models.ProductChannelListing.objects.filter(
            product_id=product_id, channel_id__in=not_available_channel_ids
        ).delete()


class ProductMediaCreateInput(graphene.InputObjectType):
    alt = graphene.String(description="Alt text for a product media.")
    image = Upload(
        required=False, description="Represents an image file in a multipart request."
    )
    product = graphene.ID(
        required=True, description="ID of an product.", name="product"
    )
    media_url = graphene.String(
        required=False, description="Represents an URL to an external media."
    )


class ProductMediaCreate(BaseMutation):
    product = graphene.Field(Product)
    media = graphene.Field(ProductMedia)

    class Arguments:
        input = ProductMediaCreateInput(
            required=True, description="Fields required to create a product media."
        )

    class Meta:
        description = (
            "Create a media object (image or video URL) associated with product. "
            "For image, this mutation must be sent as a `multipart` request. "
            "More detailed specs of the upload format can be found here: "
            "https://github.com/jaydenseric/graphql-multipart-request-spec"
        )
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def validate_input(cls, data):
        image = data.get("image")
        media_url = data.get("media_url")

        if not image and not media_url:
            raise ValidationError(
                {
                    "input": ValidationError(
                        "Image or external URL is required.",
                        code=ProductErrorCode.REQUIRED,
                    )
                }
            )
        if image and media_url:
            raise ValidationError(
                {
                    "input": ValidationError(
                        "Either image or external URL is required.",
                        code=ProductErrorCode.DUPLICATED_INPUT_ITEM,
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        data = data.get("input")
        cls.validate_input(data)
        product = cls.get_node_or_error(
            info,
            data["product"],
            field="product",
            only_type=Product,
            qs=models.Product.objects.prefetched_for_webhook(),
        )

        alt = data.get("alt", "")
        image = data.get("image")
        media_url = data.get("media_url")
        if image:
            image_data = info.context.FILES.get(image)
            validate_image_file(image_data, "image", ProductErrorCode)
            add_hash_to_file_name(image_data)
            media = product.media.create(
                image=image_data, alt=alt, type=ProductMediaTypes.IMAGE
            )
        if media_url:
            # Remote URLs can point to the images or oembed data.
            # In case of images, file is downloaded. Otherwise we keep only
            # URL to remote media.
            if is_image_url(media_url):
                validate_image_url(media_url, "media_url", ProductErrorCode.INVALID)
                filename = get_filename_from_url(media_url)
                image_data = requests.get(media_url, stream=True)
                image_file = File(image_data.raw, filename)
                media = product.media.create(
                    image=image_file,
                    alt=alt,
                    type=ProductMediaTypes.IMAGE,
                )
            else:
                oembed_data, media_type = get_oembed_data(media_url, "media_url")
                media = product.media.create(
                    external_url=oembed_data["url"],
                    alt=oembed_data.get("title", alt),
                    type=media_type,
                    oembed_data=oembed_data,
                )

        info.context.plugins.product_updated(product)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductMediaCreate(product=product, media=media)


class ProductMediaUpdateInput(graphene.InputObjectType):
    alt = graphene.String(description="Alt text for a product media.")


class ProductMediaUpdate(BaseMutation):
    product = graphene.Field(Product)
    media = graphene.Field(ProductMedia)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a product media to update.")
        input = ProductMediaUpdateInput(
            required=True, description="Fields required to update a product media."
        )

    class Meta:
        description = "Updates a product media."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        media = cls.get_node_or_error(info, data.get("id"), only_type=ProductMedia)
        product = models.Product.objects.prefetched_for_webhook().get(
            pk=media.product_id
        )
        alt = data.get("input").get("alt")
        if alt is not None:
            media.alt = alt
            media.save(update_fields=["alt"])
        info.context.plugins.product_updated(product)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductMediaUpdate(product=product, media=media)


class ProductMediaReorder(BaseMutation):
    product = graphene.Field(Product)
    media = NonNullList(ProductMedia)

    class Arguments:
        product_id = graphene.ID(
            required=True,
            description="ID of product that media order will be altered.",
        )
        media_ids = NonNullList(
            graphene.ID,
            required=True,
            description="IDs of a product media in the desired order.",
        )

    class Meta:
        description = "Changes ordering of the product media."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, product_id, media_ids):
        product = cls.get_node_or_error(
            info,
            product_id,
            field="product_id",
            only_type=Product,
            qs=models.Product.objects.prefetched_for_webhook(),
        )

        if len(media_ids) != product.media.count():
            raise ValidationError(
                {
                    "order": ValidationError(
                        "Incorrect number of media IDs provided.",
                        code=ProductErrorCode.INVALID,
                    )
                }
            )

        ordered_media = []
        for media_id in media_ids:
            media = cls.get_node_or_error(
                info, media_id, field="order", only_type=ProductMedia
            )
            if media and media.product != product:
                raise ValidationError(
                    {
                        "order": ValidationError(
                            "Media %(media_id)s does not belong to this product.",
                            code=ProductErrorCode.NOT_PRODUCTS_IMAGE,
                            params={"media_id": media_id},
                        )
                    }
                )
            ordered_media.append(media)

        update_ordered_media(ordered_media)

        info.context.plugins.product_updated(product)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductMediaReorder(product=product, media=ordered_media)


class ProductVariantSetDefault(BaseMutation):
    product = graphene.Field(Product)

    class Arguments:
        product_id = graphene.ID(
            required=True,
            description="Id of a product that will have the default variant set.",
        )
        variant_id = graphene.ID(
            required=True,
            description="Id of a variant that will be set as default.",
        )

    class Meta:
        description = (
            "Set default variant for a product. "
            "Mutation triggers PRODUCT_UPDATED webhook."
        )
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, product_id, variant_id):
        qs = models.Product.objects.prefetched_for_webhook()
        product = cls.get_node_or_error(
            info, product_id, field="product_id", only_type=Product, qs=qs
        )
        variant = cls.get_node_or_error(
            info,
            variant_id,
            field="variant_id",
            only_type=ProductVariant,
            qs=models.ProductVariant.objects.select_related("product"),
        )
        if variant.product != product:
            raise ValidationError(
                {
                    "variant_id": ValidationError(
                        "Provided variant doesn't belong to provided product.",
                        code=ProductErrorCode.NOT_PRODUCTS_VARIANT,
                    )
                }
            )
        product.default_variant = variant
        product.save(update_fields=["default_variant", "updated_at"])
        info.context.plugins.product_updated(product)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductVariantSetDefault(product=product)


class ProductVariantReorder(BaseMutation):
    product = graphene.Field(Product)

    class Arguments:
        product_id = graphene.ID(
            required=True,
            description="Id of product that variants order will be altered.",
        )
        moves = NonNullList(
            ReorderInput,
            required=True,
            description="The list of variant reordering operations.",
        )

    class Meta:
        description = (
            "Reorder the variants of a product. "
            "Mutation updates updated_at on product and "
            "triggers PRODUCT_UPDATED webhook."
        )
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, product_id, moves):
        pk = cls.get_global_id_or_error(product_id, only_type=Product)

        try:
            product = models.Product.objects.prefetched_for_webhook().get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "product_id": ValidationError(
                        (f"Couldn't resolve to a product type: {product_id}"),
                        code=ProductErrorCode.NOT_FOUND,
                    )
                }
            )

        variants_m2m = product.variants
        operations = {}

        for move_info in moves:
            variant_pk = cls.get_global_id_or_error(
                move_info.id, only_type=ProductVariant, field="moves"
            )

            try:
                m2m_info = variants_m2m.get(id=int(variant_pk))
            except ObjectDoesNotExist:
                raise ValidationError(
                    {
                        "moves": ValidationError(
                            f"Couldn't resolve to a variant: {move_info.id}",
                            code=ProductErrorCode.NOT_FOUND,
                        )
                    }
                )
            operations[m2m_info.pk] = move_info.sort_order

        with traced_atomic_transaction():
            perform_reordering(variants_m2m, operations)

        product.save(update_fields=["updated_at", "updated_at"])
        info.context.plugins.product_updated(product)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductVariantReorder(product=product)


class ProductMediaDelete(BaseMutation):
    product = graphene.Field(Product)
    media = graphene.Field(ProductMedia)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a product media to delete.")

    class Meta:
        description = "Deletes a product media."

        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        media_obj = cls.get_node_or_error(info, data.get("id"), only_type=ProductMedia)
        media_id = media_obj.id
        media_obj.delete()
        media_obj.id = media_id
        product = models.Product.objects.prefetched_for_webhook().get(
            pk=media_obj.product_id
        )
        info.context.plugins.product_updated(product)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductMediaDelete(product=product, media=media_obj)


class VariantMediaAssign(BaseMutation):
    product_variant = graphene.Field(ProductVariant)
    media = graphene.Field(ProductMedia)

    class Arguments:
        media_id = graphene.ID(
            required=True, description="ID of a product media to assign to a variant."
        )
        variant_id = graphene.ID(required=True, description="ID of a product variant.")

    class Meta:
        description = "Assign an media to a product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, media_id, variant_id):
        media = cls.get_node_or_error(
            info, media_id, field="media_id", only_type=ProductMedia
        )
        qs = models.ProductVariant.objects.prefetched_for_webhook()
        variant = cls.get_node_or_error(
            info, variant_id, field="variant_id", only_type=ProductVariant, qs=qs
        )
        if media and variant:
            # check if the given image and variant can be matched together
            media_belongs_to_product = variant.product.media.filter(pk=media.pk).first()
            if media_belongs_to_product:
                _, created = media.variant_media.get_or_create(variant=variant)
                if not created:
                    raise ValidationError(
                        {
                            "media_id": ValidationError(
                                "This media is already assigned",
                                code=ProductErrorCode.MEDIA_ALREADY_ASSIGNED,
                            )
                        }
                    )
            else:
                raise ValidationError(
                    {
                        "media_id": ValidationError(
                            "This media doesn't belong to that product.",
                            code=ProductErrorCode.NOT_PRODUCTS_IMAGE,
                        )
                    }
                )
        variant = ChannelContext(node=variant, channel_slug=None)
        transaction.on_commit(
            lambda: info.context.plugins.product_variant_updated(variant.node)
        )
        return VariantMediaAssign(product_variant=variant, media=media)


class VariantMediaUnassign(BaseMutation):
    product_variant = graphene.Field(ProductVariant)
    media = graphene.Field(ProductMedia)

    class Arguments:
        media_id = graphene.ID(
            required=True,
            description="ID of a product media to unassign from a variant.",
        )
        variant_id = graphene.ID(required=True, description="ID of a product variant.")

    class Meta:
        description = "Unassign an media from a product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, media_id, variant_id):
        media = cls.get_node_or_error(
            info, media_id, field="image_id", only_type=ProductMedia
        )
        qs = models.ProductVariant.objects.prefetched_for_webhook()
        variant = cls.get_node_or_error(
            info, variant_id, field="variant_id", only_type=ProductVariant, qs=qs
        )

        try:
            variant_media = models.VariantMedia.objects.get(
                media=media, variant=variant
            )
        except models.VariantMedia.DoesNotExist:
            raise ValidationError(
                {
                    "media_id": ValidationError(
                        "Media is not assigned to this variant.",
                        code=ProductErrorCode.NOT_PRODUCTS_IMAGE,
                    )
                }
            )
        else:
            variant_media.delete()

        variant = ChannelContext(node=variant, channel_slug=None)
        transaction.on_commit(
            lambda: info.context.plugins.product_variant_updated(variant.node)
        )
        return VariantMediaUnassign(product_variant=variant, media=media)


class ProductVariantPreorderDeactivate(BaseMutation):
    product_variant = graphene.Field(
        ProductVariant, description="Product variant with ended preorder."
    )

    class Arguments:
        id = graphene.ID(
            required=True,
            description="ID of a variant which preorder should be deactivated.",
        )

    class Meta:
        description = (
            "Deactivates product variant preorder. "
            "It changes all preorder allocation into regular allocation."
            + ADDED_IN_31
            + PREVIEW_FEATURE
        )
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, _root, info, id):
        qs = models.ProductVariant.objects.prefetched_for_webhook()
        variant = cls.get_node_or_error(
            info, id, field="id", only_type=ProductVariant, qs=qs
        )
        if not variant.is_preorder:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "This variant is not in preorder.",
                        code=ProductErrorCode.INVALID,
                    )
                }
            )

        try:
            deactivate_preorder_for_variant(variant)
        except PreorderAllocationError as error:
            raise ValidationError(
                str(error),
                code=ProductErrorCode.PREORDER_VARIANT_CANNOT_BE_DEACTIVATED,
            )

        variant = ChannelContext(node=variant, channel_slug=None)
        transaction.on_commit(
            lambda: info.context.plugins.product_variant_updated(variant.node)
        )
        return ProductVariantPreorderDeactivate(product_variant=variant)
