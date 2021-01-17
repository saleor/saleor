import datetime
from collections import defaultdict
from typing import List, Tuple

import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.utils.text import slugify
from graphene.types import InputObjectType

from ....attribute import AttributeInputType, AttributeType
from ....attribute import models as attribute_models
from ....core.exceptions import PermissionDenied
from ....core.permissions import ProductPermissions, ProductTypePermissions
from ....order import OrderStatus
from ....order import models as order_models
from ....product import models
from ....product.error_codes import CollectionErrorCode, ProductErrorCode
from ....product.tasks import (
    update_product_discounted_price_task,
    update_products_discounted_prices_of_catalogues_task,
    update_variants_names,
)
from ....product.thumbnails import (
    create_category_background_image_thumbnails,
    create_collection_background_image_thumbnails,
    create_product_thumbnails,
)
from ....product.utils import delete_categories, get_products_ids_without_variants
from ....product.utils.variants import generate_and_set_variant_name
from ...attribute.utils import AttributeAssignmentMixin, AttrValuesInput
from ...channel import ChannelContext
from ...core.inputs import ReorderInput
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.scalars import WeightScalar
from ...core.types import SeoInput, Upload
from ...core.types.common import CollectionError, ProductError
from ...core.utils import (
    clean_seo_fields,
    from_global_id_strict_type,
    get_duplicated_values,
    validate_image_file,
    validate_slug_and_generate_if_needed,
)
from ...core.utils.reordering import perform_reordering
from ...warehouse.types import Warehouse
from ..types import (
    Category,
    Collection,
    Product,
    ProductImage,
    ProductType,
    ProductVariant,
)
from ..utils import (
    create_stocks,
    get_used_attribute_values_for_variant,
    get_used_variants_attribute_values,
)


class CategoryInput(graphene.InputObjectType):
    description = graphene.String(description="Category description (HTML/text).")
    description_json = graphene.JSONString(description="Category description (JSON).")
    name = graphene.String(description="Category name.")
    slug = graphene.String(description="Category slug.")
    seo = SeoInput(description="Search engine optimization fields.")
    background_image = Upload(description="Background image file.")
    background_image_alt = graphene.String(description="Alt text for an image.")


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
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
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
            validate_image_file(image_data, "background_image")
        clean_seo_fields(cleaned_input)
        return cleaned_input

    @classmethod
    def perform_mutation(cls, root, info, **data):
        parent_id = data.pop("parent_id", None)
        data["input"]["parent_id"] = parent_id
        return super().perform_mutation(root, info, **data)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        if cleaned_input.get("background_image"):
            create_category_background_image_thumbnails.delay(instance.pk)


class CategoryUpdate(CategoryCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a category to update.")
        input = CategoryInput(
            required=True, description="Fields required to update a category."
        )

    class Meta:
        description = "Updates a category."
        model = models.Category
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"


class CategoryDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a category to delete.")

    class Meta:
        description = "Deletes a category."
        model = models.Category
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        if not cls.check_permissions(info.context):
            raise PermissionDenied()
        node_id = data.get("id")
        instance = cls.get_node_or_error(info, node_id, only_type=Category)

        db_id = instance.id

        delete_categories([db_id])

        instance.id = db_id
        return cls.success_response(instance)


class CollectionInput(graphene.InputObjectType):
    is_published = graphene.Boolean(
        description="Informs whether a collection is published."
    )
    name = graphene.String(description="Name of the collection.")
    slug = graphene.String(description="Slug of the collection.")
    description = graphene.String(
        description="Description of the collection (HTML/text)."
    )
    description_json = graphene.JSONString(
        description="Description of the collection (JSON)."
    )
    background_image = Upload(description="Background image file.")
    background_image_alt = graphene.String(description="Alt text for an image.")
    seo = SeoInput(description="Search engine optimization fields.")
    publication_date = graphene.Date(description="Publication date. ISO 8601 standard.")


class CollectionCreateInput(CollectionInput):
    products = graphene.List(
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
            validate_image_file(image_data, "background_image")
        is_published = cleaned_input.get("is_published")
        publication_date = cleaned_input.get("publication_date")
        if is_published and not publication_date:
            cleaned_input["publication_date"] = datetime.date.today()
        clean_seo_fields(cleaned_input)
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        if cleaned_input.get("background_image"):
            create_collection_background_image_thumbnails.delay(instance.pk)

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
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    def save(cls, info, instance, cleaned_input):
        if cleaned_input.get("background_image"):
            create_collection_background_image_thumbnails.delay(instance.pk)
        instance.save()


class CollectionDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a collection to delete.")

    class Meta:
        description = "Deletes a collection."
        model = models.Collection
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **kwargs):
        result = super().perform_mutation(_root, info, **kwargs)
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
        moves = graphene.List(
            MoveProductInput,
            required=True,
            description="The collection products position operations.",
        )

    @classmethod
    def perform_mutation(cls, _root, info, collection_id, moves):
        pk = from_global_id_strict_type(
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
            product_pk = from_global_id_strict_type(
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

        with transaction.atomic():
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
        products = graphene.List(
            graphene.ID, required=True, description="List of product IDs."
        )

    class Meta:
        description = "Adds products to a collection."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = CollectionError
        error_type_field = "collection_errors"

    @classmethod
    @transaction.atomic()
    def perform_mutation(cls, _root, info, collection_id, products):
        collection = cls.get_node_or_error(
            info, collection_id, field="collection_id", only_type=Collection
        )
        products = cls.get_nodes_or_error(products, "products", Product)
        cls.clean_products(products)
        collection.products.add(*products)
        if collection.sale_set.exists():
            # Updated the db entries, recalculating discounts of affected products
            update_products_discounted_prices_of_catalogues_task.delay(
                product_ids=[pq.pk for pq in products]
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
        products = graphene.List(
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
        products = cls.get_nodes_or_error(products, "products", only_type=Product)
        collection.products.remove(*products)
        if collection.sale_set.exists():
            # Updated the db entries, recalculating discounts of affected products
            update_products_discounted_prices_of_catalogues_task.delay(
                product_ids=[p.pk for p in products]
            )
        return CollectionRemoveProducts(
            collection=ChannelContext(node=collection, channel_slug=None)
        )


class AttributeValueInput(InputObjectType):
    id = graphene.ID(description="ID of the selected attribute.")
    values = graphene.List(
        graphene.String,
        required=False,
        description=(
            "The value or slug of an attribute to resolve. "
            "If the passed value is non-existent, it will be created."
        ),
    )
    file = graphene.String(
        required=False,
        description="URL of the file attribute. Every time, a new value is created.",
    )
    content_type = graphene.String(required=False, description="File content type.")
    references = graphene.List(
        graphene.NonNull(graphene.ID),
        description="List of entity IDs that will be used as references.",
        required=False,
    )


class ProductInput(graphene.InputObjectType):
    attributes = graphene.List(AttributeValueInput, description="List of attributes.")
    category = graphene.ID(description="ID of the product's category.", name="category")
    charge_taxes = graphene.Boolean(
        description="Determine if taxes are being charged for the product."
    )
    collections = graphene.List(
        graphene.ID,
        description="List of IDs of collections that the product belongs to.",
        name="collections",
    )
    description = graphene.String(description="Product description (HTML/text).")
    description_json = graphene.JSONString(description="Product description (JSON).")
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
    quantity = graphene.Int(description="Quantity of items available for sell.")


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
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def clean_attributes(
        cls, attributes: dict, product_type: models.ProductType
    ) -> T_INPUT_MAP:
        attributes_qs = product_type.product_attributes
        attributes = AttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, is_variant=False
        )
        return attributes

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)

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

        # FIXME  tax_rate logic should be dropped after we remove tax_rate from input
        tax_rate = cleaned_input.pop("tax_rate", "")
        if tax_rate:
            info.context.plugins.assign_tax_code_to_object_meta(instance, tax_rate)

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
    @transaction.atomic
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
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        product = getattr(response, cls._meta.return_field_name)
        info.context.plugins.product_created(product)

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
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    @transaction.atomic
    def save(cls, info, instance, cleaned_input):
        instance.save()
        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)
        info.context.plugins.product_updated(instance)


class ProductDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product to delete.")

    class Meta:
        description = "Deletes a product."
        model = models.Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def success_response(cls, instance):
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")
        instance = cls.get_node_or_error(info, node_id, only_type=Product)

        # get draft order lines for variant
        line_pks = list(
            order_models.OrderLine.objects.filter(
                variant__in=instance.variants.all(), order__status=OrderStatus.DRAFT
            ).values_list("pk", flat=True)
        )

        response = super().perform_mutation(_root, info, **data)

        # delete order lines for deleted variant
        order_models.OrderLine.objects.filter(pk__in=line_pks).delete()

        return response


class ProductVariantInput(graphene.InputObjectType):
    attributes = graphene.List(
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


class ProductVariantCreateInput(ProductVariantInput):
    attributes = graphene.List(
        AttributeValueInput,
        required=True,
        description="List of attributes specific to this variant.",
    )
    product = graphene.ID(
        description="Product ID of which type is the variant.",
        name="product",
        required=True,
    )
    stocks = graphene.List(
        graphene.NonNull(StockInput),
        description=("Stocks of a product available for sale."),
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
            attributes, attributes_qs, is_variant=True
        )
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
                ProductErrorCode.DUPLICATED_INPUT_ITEM,
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

        # Run the validation only if product type is configurable
        if product_type.has_variants:
            # Attributes are provided as list of `AttributeValueInput` objects.
            # We need to transform them into the format they're stored in the
            # `Product` model, which is HStore field that maps attribute's PK to
            # the value's PK.
            attributes = cleaned_input.get("attributes")
            try:
                if attributes:
                    cleaned_attributes = cls.clean_attributes(attributes, product_type)
                    cls.validate_duplicated_attribute_values(
                        cleaned_attributes, used_attribute_values, instance
                    )
                    cleaned_input["attributes"] = cleaned_attributes
                elif not instance.pk and not attributes:
                    # if attributes were not provided on creation
                    raise ValidationError(
                        "All attributes must take a value.",
                        ProductErrorCode.REQUIRED.value,
                    )
            except ValidationError as exc:
                raise ValidationError({"attributes": exc})

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
    @transaction.atomic()
    def save(cls, info, instance, cleaned_input):
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
        info.context.plugins.product_updated(instance.product)

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
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
        errors_mapping = {"price_amount": "price"}

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
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def success_response(cls, instance):
        # Update the "discounted_prices" of the parent product
        update_product_discounted_price_task.delay(instance.product_id)
        product = models.Product.objects.get(id=instance.product_id)
        # if the product default variant has been removed set the new one
        if not product.default_variant:
            product.default_variant = product.variants.first()
            product.save(update_fields=["default_variant"])
        instance = ChannelContext(node=instance, channel_slug=None)
        return super().success_response(instance)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")
        variant_pk = from_global_id_strict_type(node_id, ProductVariant, field="pk")

        # get draft order lines for variant
        line_pks = list(
            order_models.OrderLine.objects.filter(
                variant__pk=variant_pk, order__status=OrderStatus.DRAFT
            ).values_list("pk", flat=True)
        )

        response = super().perform_mutation(_root, info, **data)

        # delete order lines for deleted variant
        order_models.OrderLine.objects.filter(pk__in=line_pks).delete()

        return response


class ProductTypeInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the product type.")
    slug = graphene.String(description="Product type slug.")
    has_variants = graphene.Boolean(
        description=(
            "Determines if product of this type has multiple variants. This option "
            "mainly simplifies product management in the dashboard. There is always at "
            "least one variant created under the hood."
        )
    )
    product_attributes = graphene.List(
        graphene.ID,
        description="List of attributes shared among all product variants.",
        name="productAttributes",
    )
    variant_attributes = graphene.List(
        graphene.ID,
        description=(
            "List of attributes used to distinguish between different variants of "
            "a product."
        ),
        name="variantAttributes",
    )
    is_shipping_required = graphene.Boolean(
        description="Determines if shipping is required for products of this variant."
    )
    is_digital = graphene.Boolean(
        description="Determines if products are digital.", required=False
    )
    weight = WeightScalar(description="Weight of the ProductType items.")
    tax_code = graphene.String(description="Tax rate for enabled tax gateway.")


class ProductTypeCreate(ModelMutation):
    class Arguments:
        input = ProductTypeInput(
            required=True, description="Fields required to create a product type."
        )

    class Meta:
        description = "Creates a new product type."
        model = models.ProductType
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)

        weight = cleaned_input.get("weight")
        if weight and weight.value < 0:
            raise ValidationError(
                {
                    "weight": ValidationError(
                        "Product type can't have negative weight.",
                        code=ProductErrorCode.INVALID,
                    )
                }
            )

        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = ProductErrorCode.REQUIRED.value
            raise ValidationError({"slug": error})

        # FIXME  tax_rate logic should be dropped after we remove tax_rate from input
        tax_rate = cleaned_input.pop("tax_rate", "")
        if tax_rate:
            instance.store_value_in_metadata(
                {"vatlayer.code": tax_rate, "description": tax_rate}
            )
            info.context.plugins.assign_tax_code_to_object_meta(instance, tax_rate)

        tax_code = cleaned_input.pop("tax_code", "")
        if tax_code:
            info.context.plugins.assign_tax_code_to_object_meta(instance, tax_code)

        cls.validate_attributes(cleaned_input)

        return cleaned_input

    @classmethod
    def validate_attributes(cls, cleaned_data):
        errors = {}
        for field in ["product_attributes", "variant_attributes"]:
            attributes = cleaned_data.get(field)
            if not attributes:
                continue
            not_valid_attributes = [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in attributes
                if attr.type != AttributeType.PRODUCT_TYPE
            ]
            if not_valid_attributes:
                errors[field] = ValidationError(
                    "Only Product type attributes are allowed.",
                    code=ProductErrorCode.INVALID.value,
                    params={"attributes": not_valid_attributes},
                )
        if errors:
            raise ValidationError(errors)

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        product_attributes = cleaned_data.get("product_attributes")
        variant_attributes = cleaned_data.get("variant_attributes")
        if product_attributes is not None:
            instance.product_attributes.set(product_attributes)
        if variant_attributes is not None:
            instance.variant_attributes.set(variant_attributes)


class ProductTypeUpdate(ProductTypeCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product type to update.")
        input = ProductTypeInput(
            required=True, description="Fields required to update a product type."
        )

    class Meta:
        description = "Updates an existing product type."
        model = models.ProductType
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def save(cls, info, instance, cleaned_input):
        variant_attr = cleaned_input.get("variant_attributes")
        if variant_attr:
            variant_attr = set(variant_attr)
            variant_attr_ids = [attr.pk for attr in variant_attr]
            update_variants_names.delay(instance.pk, variant_attr_ids)
        super().save(info, instance, cleaned_input)


class ProductTypeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product type to delete.")

    class Meta:
        description = "Deletes a product type."
        model = models.ProductType
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        node_id = data.get("id")
        product_type_pk = from_global_id_strict_type(node_id, ProductType, field="pk")
        variants_pks = models.Product.objects.filter(
            product_type__pk=product_type_pk
        ).values_list("variants__pk", flat=True)
        # get draft order lines for products
        order_line_pks = list(
            order_models.OrderLine.objects.filter(
                variant__pk__in=variants_pks, order__status=OrderStatus.DRAFT
            ).values_list("pk", flat=True)
        )

        response = super().perform_mutation(_root, info, **data)

        # delete order lines for deleted variants
        order_models.OrderLine.objects.filter(pk__in=order_line_pks).delete()

        return response


class ProductImageCreateInput(graphene.InputObjectType):
    alt = graphene.String(description="Alt text for an image.")
    image = Upload(
        required=True, description="Represents an image file in a multipart request."
    )
    product = graphene.ID(
        required=True, description="ID of an product.", name="product"
    )


class ProductImageCreate(BaseMutation):
    product = graphene.Field(Product)
    image = graphene.Field(ProductImage)

    class Arguments:
        input = ProductImageCreateInput(
            required=True, description="Fields required to create a product image."
        )

    class Meta:
        description = (
            "Create a product image. This mutation must be sent as a `multipart` "
            "request. More detailed specs of the upload format can be found here: "
            "https://github.com/jaydenseric/graphql-multipart-request-spec"
        )
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        data = data.get("input")
        product = cls.get_node_or_error(
            info, data["product"], field="product", only_type=Product
        )

        image_data = info.context.FILES.get(data["image"])
        validate_image_file(image_data, "image")

        image = product.images.create(image=image_data, alt=data.get("alt", ""))
        create_product_thumbnails.delay(image.pk)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductImageCreate(product=product, image=image)


class ProductImageUpdateInput(graphene.InputObjectType):
    alt = graphene.String(description="Alt text for an image.")


class ProductImageUpdate(BaseMutation):
    product = graphene.Field(Product)
    image = graphene.Field(ProductImage)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a product image to update.")
        input = ProductImageUpdateInput(
            required=True, description="Fields required to update a product image."
        )

    class Meta:
        description = "Updates a product image."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        image = cls.get_node_or_error(info, data.get("id"), only_type=ProductImage)
        product = image.product
        alt = data.get("input").get("alt")
        if alt is not None:
            image.alt = alt
            image.save(update_fields=["alt"])
        product = ChannelContext(node=product, channel_slug=None)
        return ProductImageUpdate(product=product, image=image)


class ProductImageReorder(BaseMutation):
    product = graphene.Field(Product)
    images = graphene.List(ProductImage)

    class Arguments:
        product_id = graphene.ID(
            required=True,
            description="Id of product that images order will be altered.",
        )
        images_ids = graphene.List(
            graphene.ID,
            required=True,
            description="IDs of a product images in the desired order.",
        )

    class Meta:
        description = "Changes ordering of the product image."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, product_id, images_ids):
        product = cls.get_node_or_error(
            info, product_id, field="product_id", only_type=Product
        )
        if len(images_ids) != product.images.count():
            raise ValidationError(
                {
                    "order": ValidationError(
                        "Incorrect number of image IDs provided.",
                        code=ProductErrorCode.INVALID,
                    )
                }
            )

        images = []
        for image_id in images_ids:
            image = cls.get_node_or_error(
                info, image_id, field="order", only_type=ProductImage
            )
            if image and image.product != product:
                raise ValidationError(
                    {
                        "order": ValidationError(
                            "Image %(image_id)s does not belong to this product.",
                            code=ProductErrorCode.NOT_PRODUCTS_IMAGE,
                            params={"image_id": image_id},
                        )
                    }
                )
            images.append(image)

        for order, image in enumerate(images):
            image.sort_order = order
            image.save(update_fields=["sort_order"])

        product = ChannelContext(node=product, channel_slug=None)
        return ProductImageReorder(product=product, images=images)


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
        product = cls.get_node_or_error(
            info, product_id, field="product_id", only_type=Product
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
        moves = graphene.List(
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
        pk = from_global_id_strict_type(product_id, only_type=Product, field="id")

        try:
            product = models.Product.objects.prefetch_related("variants").get(pk=pk)
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
            variant_pk = from_global_id_strict_type(
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

        with transaction.atomic():
            perform_reordering(variants_m2m, operations)

        product.save(update_fields=["updated_at"])
        info.context.plugins.product_updated(product)
        product = ChannelContext(node=product, channel_slug=None)
        return ProductVariantReorder(product=product)


class ProductImageDelete(BaseMutation):
    product = graphene.Field(Product)
    image = graphene.Field(ProductImage)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a product image to delete.")

    class Meta:
        description = "Deletes a product image."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        image = cls.get_node_or_error(info, data.get("id"), only_type=ProductImage)
        image_id = image.id
        image.delete()
        image.id = image_id
        product = ChannelContext(node=image.product, channel_slug=None)
        return ProductImageDelete(product=product, image=image)


class VariantImageAssign(BaseMutation):
    product_variant = graphene.Field(ProductVariant)
    image = graphene.Field(ProductImage)

    class Arguments:
        image_id = graphene.ID(
            required=True, description="ID of a product image to assign to a variant."
        )
        variant_id = graphene.ID(required=True, description="ID of a product variant.")

    class Meta:
        description = "Assign an image to a product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, image_id, variant_id):
        image = cls.get_node_or_error(
            info, image_id, field="image_id", only_type=ProductImage
        )
        variant = cls.get_node_or_error(
            info, variant_id, field="variant_id", only_type=ProductVariant
        )
        if image and variant:
            # check if the given image and variant can be matched together
            image_belongs_to_product = variant.product.images.filter(
                pk=image.pk
            ).first()
            if image_belongs_to_product:
                image.variant_images.create(variant=variant)
            else:
                raise ValidationError(
                    {
                        "image_id": ValidationError(
                            "This image doesn't belong to that product.",
                            code=ProductErrorCode.NOT_PRODUCTS_IMAGE,
                        )
                    }
                )
        variant = ChannelContext(node=variant, channel_slug=None)
        return VariantImageAssign(product_variant=variant, image=image)


class VariantImageUnassign(BaseMutation):
    product_variant = graphene.Field(ProductVariant)
    image = graphene.Field(ProductImage)

    class Arguments:
        image_id = graphene.ID(
            required=True,
            description="ID of a product image to unassign from a variant.",
        )
        variant_id = graphene.ID(required=True, description="ID of a product variant.")

    class Meta:
        description = "Unassign an image from a product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, image_id, variant_id):
        image = cls.get_node_or_error(
            info, image_id, field="image_id", only_type=ProductImage
        )
        variant = cls.get_node_or_error(
            info, variant_id, field="variant_id", only_type=ProductVariant
        )

        try:
            variant_image = models.VariantImage.objects.get(
                image=image, variant=variant
            )
        except models.VariantImage.DoesNotExist:
            raise ValidationError(
                {
                    "image_id": ValidationError(
                        "Image is not assigned to this variant.",
                        code=ProductErrorCode.NOT_PRODUCTS_IMAGE,
                    )
                }
            )
        else:
            variant_image.delete()

        variant = ChannelContext(node=variant, channel_slug=None)
        return VariantImageUnassign(product_variant=variant, image=image)
