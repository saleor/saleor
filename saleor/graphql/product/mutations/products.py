from collections import defaultdict
from typing import Iterable, List, Tuple, Union

import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Q, QuerySet
from django.template.defaultfilters import slugify
from graphene.types import InputObjectType
from graphql_jwt.exceptions import PermissionDenied
from graphql_relay import from_global_id

from ....core.permissions import ProductPermissions
from ....product import models
from ....product.error_codes import ProductErrorCode
from ....product.tasks import (
    update_product_minimal_variant_price_task,
    update_products_minimal_variant_prices_of_catalogues_task,
    update_variants_names,
)
from ....product.thumbnails import (
    create_category_background_image_thumbnails,
    create_collection_background_image_thumbnails,
    create_product_thumbnails,
)
from ....product.utils import delete_categories
from ....product.utils.attributes import (
    associate_attribute_values_to_instance,
    generate_name_for_variant,
)
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.scalars import Decimal, WeightScalar
from ...core.types import SeoInput, Upload
from ...core.types.common import ProductError
from ...core.utils import (
    clean_seo_fields,
    from_global_id_strict_type,
    get_duplicated_values,
    validate_image_file,
    validate_slug_and_generate_if_needed,
)
from ...core.utils.reordering import perform_reordering
from ...meta.deprecated.mutations import ClearMetaBaseMutation, UpdateMetaBaseMutation
from ...warehouse.types import Warehouse
from ..types import Category, Collection, Product, ProductImage, ProductVariant
from ..utils import (
    create_stocks,
    get_used_attribute_values_for_variant,
    get_used_variants_attribute_values,
    validate_attribute_input_for_product,
    validate_attribute_input_for_variant,
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
        if data.get("background_image"):
            image_data = info.context.FILES.get(data["background_image"])
            validate_image_file(image_data, "background_image")
        clean_seo_fields(cleaned_input)
        return cleaned_input

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()
        if cleaned_input.get("background_image"):
            create_collection_background_image_thumbnails.delay(instance.pk)


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
        error_type_class = ProductError
        error_type_field = "product_errors"

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
        error_type_class = ProductError
        error_type_field = "product_errors"


class MoveProductInput(graphene.InputObjectType):
    product_id = graphene.ID(
        description="The ID of the product to move.", required=True
    )
    sort_order = graphene.Int(
        description=(
            "The relative sorting position of the product (from -inf to +inf) "
            "starting from the first given product's actual position."
        )
    )


class CollectionReorderProducts(BaseMutation):
    collection = graphene.Field(
        Collection, description="Collection from which products are reordered."
    )

    class Meta:
        description = "Reorder the products of a collection."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

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
                            code=ProductErrorCode.NOT_FOUND,
                        )
                    }
                )
            operations[m2m_info.pk] = move_info.sort_order

        with transaction.atomic():
            perform_reordering(m2m_related_field, operations)
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
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    @transaction.atomic()
    def perform_mutation(cls, _root, info, collection_id, products):
        collection = cls.get_node_or_error(
            info, collection_id, field="collection_id", only_type=Collection
        )
        products = cls.get_nodes_or_error(products, "products", Product)
        collection.products.add(*products)
        if collection.sale_set.exists():
            # Updated the db entries, recalculating discounts of affected products
            update_products_minimal_variant_prices_of_catalogues_task.delay(
                product_ids=[p.pk for p in products]
            )
        return CollectionAddProducts(collection=collection)


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
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, collection_id, products):
        collection = cls.get_node_or_error(
            info, collection_id, field="collection_id", only_type=Collection
        )
        products = cls.get_nodes_or_error(products, "products", only_type=Product)
        collection.products.remove(*products)
        if collection.sale_set.exists():
            # Updated the db entries, recalculating discounts of affected products
            update_products_minimal_variant_prices_of_catalogues_task.delay(
                product_ids=[p.pk for p in products]
            )
        return CollectionRemoveProducts(collection=collection)


class CollectionUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        model = models.Collection
        description = "Update public metadata for collection."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = True
        error_type_class = ProductError
        error_type_field = "product_errors"


class CollectionClearMeta(ClearMetaBaseMutation):
    class Meta:
        model = models.Collection
        description = "Clears public metadata for collection."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = True
        error_type_class = ProductError
        error_type_field = "product_errors"


class CollectionUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        model = models.Collection
        description = "Update private metadata for collection."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = False
        error_type_class = ProductError
        error_type_field = "product_errors"


class CollectionClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        model = models.Collection
        description = "Clears private metadata item for collection."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = False
        error_type_class = ProductError
        error_type_field = "product_errors"


class CategoryUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        model = models.Category
        description = "Update public metadata for category."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = True
        error_type_class = ProductError
        error_type_field = "product_errors"


class CategoryClearMeta(ClearMetaBaseMutation):
    class Meta:
        model = models.Category
        description = "Clears public metadata for category."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = True
        error_type_class = ProductError
        error_type_field = "product_errors"


class CategoryUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        model = models.Category
        description = "Update private metadata for category."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = False
        error_type_class = ProductError
        error_type_field = "product_errors"


class CategoryClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        model = models.Category
        description = "Clears private metadata for category."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = False
        error_type_class = ProductError
        error_type_field = "product_errors"


class AttributeValueInput(InputObjectType):
    id = graphene.ID(description="ID of the selected attribute.")
    values = graphene.List(
        graphene.String,
        required=True,
        description=(
            "The value or slug of an attribute to resolve. "
            "If the passed value is non-existent, it will be created."
        ),
    )


class ProductInput(graphene.InputObjectType):
    attributes = graphene.List(AttributeValueInput, description="List of attributes.")
    publication_date = graphene.types.datetime.Date(
        description="Publication date. ISO 8601 standard."
    )
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
    is_published = graphene.Boolean(
        description="Determines if product is visible to customers."
    )
    name = graphene.String(description="Product name.")
    slug = graphene.String(description="Product slug.")
    base_price = Decimal(description="Product price.")
    tax_code = graphene.String(description="Tax rate for enabled tax gateway.")
    seo = SeoInput(description="Search engine optimization fields.")
    weight = WeightScalar(description="Weight of the Product.", required=False)
    sku = graphene.String(
        description=(
            "Stock keeping unit of a product. Note: this field is only used if "
            "a product doesn't use variants."
        )
    )
    track_inventory = graphene.Boolean(
        description=(
            "Determines if the inventory of this product should be tracked. If false, "
            "the quantity won't change when customers buy this item. Note: this field "
            "is only used if a product doesn't use variants."
        )
    )


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
    stocks = graphene.List(
        graphene.NonNull(StockInput),
        description=(
            "Stocks of a product available for sale. Note: this field is "
            "only used if a product doesn't use variants."
        ),
        required=False,
    )


T_INPUT_MAP = List[Tuple[models.Attribute, List[str]]]
T_INSTANCE = Union[models.Product, models.ProductVariant]


class AttributeAssignmentMixin:
    """Handles cleaning of the attribute input and creating the proper relations.

    1. You should first call ``clean_input``, to transform and attempt to resolve
       the provided input into actual objects. It will then perform a few
       checks to validate the operations supplied by the user are possible and allowed.
    2. Once everything is ready and all your data is saved inside a transaction,
       you shall call ``save`` with the cleaned input to build all the required
       relations. Once the ``save`` call is done, you are safe from continuing working
       or to commit the transaction.

    Note: you shall never call ``save`` outside of a transaction and never before
    the targeted instance owns a primary key. Failing to do so, the relations will
    be unable to build or might only be partially built.
    """

    @classmethod
    def _resolve_attribute_nodes(
        cls,
        qs: QuerySet,
        *,
        global_ids: List[str],
        pks: Iterable[int],
        slugs: Iterable[str],
    ):
        """Retrieve attributes nodes from given global IDs and/or slugs."""
        qs = qs.filter(Q(pk__in=pks) | Q(slug__in=slugs))
        nodes = list(qs)  # type: List[models.Attribute]

        if not nodes:
            raise ValidationError(
                (
                    f"Could not resolve to a node: ids={global_ids}"
                    f" and slugs={list(slugs)}"
                ),
                code=ProductErrorCode.NOT_FOUND.value,
            )

        nodes_pk_list = set()
        nodes_slug_list = set()
        for node in nodes:
            nodes_pk_list.add(node.pk)
            nodes_slug_list.add(node.slug)

        for pk, global_id in zip(pks, global_ids):
            if pk not in nodes_pk_list:
                raise ValidationError(
                    f"Could not resolve {global_id!r} to Attribute",
                    code=ProductErrorCode.NOT_FOUND.value,
                )

        for slug in slugs:
            if slug not in nodes_slug_list:
                raise ValidationError(
                    f"Could not resolve slug {slug!r} to Attribute",
                    code=ProductErrorCode.NOT_FOUND.value,
                )

        return nodes

    @classmethod
    def _resolve_attribute_global_id(cls, global_id: str) -> int:
        """Resolve an Attribute global ID into an internal ID (int)."""
        graphene_type, internal_id = from_global_id(global_id)  # type: str, str
        if graphene_type != "Attribute":
            raise ValidationError(
                f"Must receive an Attribute id, got {graphene_type}.",
                code=ProductErrorCode.INVALID.value,
            )
        if not internal_id.isnumeric():
            raise ValidationError(
                f"An invalid ID value was passed: {global_id}",
                code=ProductErrorCode.INVALID.value,
            )
        return int(internal_id)

    @classmethod
    def _pre_save_values(cls, attribute: models.Attribute, values: List[str]):
        """Lazy-retrieve or create the database objects from the supplied raw values."""
        get_or_create = attribute.values.get_or_create
        return tuple(
            get_or_create(
                attribute=attribute, slug=slugify(value), defaults={"name": value}
            )[0]
            for value in values
        )

    @classmethod
    def _check_input_for_product(cls, cleaned_input: T_INPUT_MAP, qs: QuerySet):
        """Check the cleaned attribute input for a product.

        An Attribute queryset is supplied.

        - ensure all required attributes are passed
        - ensure the values are correct for a product
        """
        supplied_attribute_pk = []
        for attribute, values in cleaned_input:
            validate_attribute_input_for_product(attribute, values)
            supplied_attribute_pk.append(attribute.pk)

        # Asserts all required attributes are supplied
        missing_required_filter = Q(value_required=True) & ~Q(
            pk__in=supplied_attribute_pk
        )

        if qs.filter(missing_required_filter).exists():
            raise ValidationError(
                "All attributes flagged as having a value required must be supplied.",
                code=ProductErrorCode.REQUIRED.value,
            )

    @classmethod
    def _check_input_for_variant(cls, cleaned_input: T_INPUT_MAP, qs: QuerySet):
        """Check the cleaned attribute input for a variant.

        An Attribute queryset is supplied.

        - ensure all attributes are passed
        - ensure the values are correct for a variant
        """
        if len(cleaned_input) != qs.count():
            raise ValidationError(
                "All attributes must take a value", code=ProductErrorCode.REQUIRED.value
            )

        for attribute, values in cleaned_input:
            validate_attribute_input_for_variant(attribute, values)

    @classmethod
    def _validate_input(
        cls, cleaned_input: T_INPUT_MAP, attribute_qs, is_variant: bool
    ):
        """Check if no invalid operations were supplied.

        :raises ValidationError: when an invalid operation was found.
        """
        if is_variant:
            return cls._check_input_for_variant(cleaned_input, attribute_qs)
        else:
            return cls._check_input_for_product(cleaned_input, attribute_qs)

    @classmethod
    def clean_input(
        cls, raw_input: dict, attributes_qs: QuerySet, is_variant: bool
    ) -> T_INPUT_MAP:
        """Resolve and prepare the input for further checks.

        :param raw_input: The user's attributes input.
        :param attributes_qs:
            A queryset of attributes, the attribute values must be prefetched.
            Prefetch is needed by ``_pre_save_values`` during save.
        :param is_variant: Whether the input is for a variant or a product.

        :raises ValidationError: contain the message.
        :return: The resolved data
        """

        # Mapping to associate the input values back to the resolved attribute nodes
        pks = {}
        slugs = {}

        # Temporary storage of the passed ID for error reporting
        global_ids = []

        for attribute_input in raw_input:
            global_id = attribute_input.get("id")
            slug = attribute_input.get("slug")
            values = attribute_input["values"]

            if global_id:
                internal_id = cls._resolve_attribute_global_id(global_id)
                global_ids.append(global_id)
                pks[internal_id] = values
            elif slug:
                slugs[slug] = values
            else:
                raise ValidationError(
                    "You must whether supply an ID or a slug",
                    code=ProductErrorCode.REQUIRED.value,
                )

        attributes = cls._resolve_attribute_nodes(
            attributes_qs, global_ids=global_ids, pks=pks.keys(), slugs=slugs.keys()
        )
        cleaned_input = []
        for attribute in attributes:
            key = pks.get(attribute.pk, None)

            # Retrieve the primary key by slug if it
            # was not resolved through a global ID but a slug
            if key is None:
                key = slugs[attribute.slug]

            cleaned_input.append((attribute, key))
        cls._validate_input(cleaned_input, attributes_qs, is_variant)
        return cleaned_input

    @classmethod
    def save(cls, instance: T_INSTANCE, cleaned_input: T_INPUT_MAP):
        """Save the cleaned input into the database against the given instance.

        Note: this should always be ran inside a transaction.

        :param instance: the product or variant to associate the attribute against.
        :param cleaned_input: the cleaned user input (refer to clean_attributes)
        """
        for attribute, values in cleaned_input:
            attribute_values = cls._pre_save_values(attribute, values)
            associate_attribute_values_to_instance(
                instance, attribute, *attribute_values
            )


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
                        code=ProductErrorCode.INVALID,
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
        # Try to get price from "basePrice" or "price" field. Once "price" is removed
        # from the schema, only "basePrice" should be used here.
        price = data.get("base_price", data.get("price"))
        if price is not None:
            if price < 0:
                raise ValidationError(
                    {
                        "basePrice": ValidationError(
                            "Product base price cannot be lower than 0.",
                            code=ProductErrorCode.INVALID,
                        )
                    }
                )
            cleaned_input["price_amount"] = price
            if instance.minimal_variant_price_amount is None:
                # Set the default "minimal_variant_price" to the "price"
                cleaned_input["minimal_variant_price_amount"] = price

        # FIXME  tax_rate logic should be dropped after we remove tax_rate from input
        tax_rate = cleaned_input.pop("tax_rate", "")
        if tax_rate:
            info.context.plugins.assign_tax_code_to_object_meta(instance, tax_rate)

        tax_code = cleaned_input.pop("tax_code", "")
        if tax_code:
            info.context.plugins.assign_tax_code_to_object_meta(instance, tax_code)

        if attributes and product_type:
            try:
                cleaned_input["attributes"] = cls.clean_attributes(
                    attributes, product_type
                )
            except ValidationError as exc:
                raise ValidationError({"attributes": exc})

        is_published = cleaned_input.get("is_published")
        category = cleaned_input.get("category")
        if not category and is_published:
            raise ValidationError(
                {
                    "isPublished": ValidationError(
                        "You must select a category to be able to publish"
                    )
                }
            )

        clean_seo_fields(cleaned_input)
        cls.clean_sku(product_type, cleaned_input)
        stocks = cleaned_input.get("stocks")
        if stocks:
            cls.check_for_duplicates_in_stocks(stocks)
        return cleaned_input

    @classmethod
    def clean_sku(cls, product_type, cleaned_input):
        """Validate SKU input field.

        When creating products that don't use variants, SKU is required in
        the input in order to create the default variant underneath.
        See the documentation for `has_variants` field for details:
        http://docs.getsaleor.com/en/latest/architecture/products.html#product-types
        """
        if product_type and not product_type.has_variants:
            input_sku = cleaned_input.get("sku")
            if not input_sku:
                raise ValidationError(
                    {
                        "sku": ValidationError(
                            "This field cannot be blank.",
                            code=ProductErrorCode.REQUIRED,
                        )
                    }
                )
            elif models.ProductVariant.objects.filter(sku=input_sku).exists():
                raise ValidationError(
                    {
                        "sku": ValidationError(
                            "Product with this SKU already exists.",
                            code=ProductErrorCode.ALREADY_EXISTS,
                        )
                    }
                )

    @classmethod
    def check_for_duplicates_in_stocks(cls, stocks_data):
        warehouse_ids = [stock["warehouse"] for stock in stocks_data]
        duplicates = get_duplicated_values(warehouse_ids)
        if duplicates:
            error_msg = "Duplicated warehouse ID: {}".format(duplicates.join(", "))
            raise ValidationError(
                {"stocks": ValidationError(error_msg, code=ProductErrorCode.UNIQUE)}
            )

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
        if not instance.product_type.has_variants:
            site_settings = info.context.site.settings
            track_inventory = cleaned_input.get(
                "track_inventory", site_settings.track_inventory_by_default
            )
            sku = cleaned_input.get("sku")
            variant = models.ProductVariant.objects.create(
                product=instance, track_inventory=track_inventory, sku=sku
            )
            stocks = cleaned_input.get("stocks")
            if stocks:
                cls.create_variant_stocks(variant, stocks)

        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)

    @classmethod
    def create_variant_stocks(cls, variant, stocks):
        warehouse_ids = [stock["warehouse"] for stock in stocks]
        warehouses = cls.get_nodes_or_error(
            warehouse_ids, "warehouse", only_type=Warehouse
        )
        create_stocks(variant, stocks, warehouses)

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        collections = cleaned_data.get("collections", None)
        if collections is not None:
            instance.collections.set(collections)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        response = super().perform_mutation(_root, info, **data)
        info.context.plugins.product_created(response.product)
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
    def clean_sku(cls, product_type, cleaned_input):
        input_sku = cleaned_input.get("sku")
        if (
            not product_type.has_variants
            and input_sku
            and models.ProductVariant.objects.filter(sku=input_sku).exists()
        ):
            raise ValidationError(
                {
                    "sku": ValidationError(
                        "Product with this SKU already exists.",
                        code=ProductErrorCode.ALREADY_EXISTS,
                    )
                }
            )

    @classmethod
    @transaction.atomic
    def save(cls, info, instance, cleaned_input):
        instance.save()
        if not instance.product_type.has_variants:
            variant = instance.variants.first()
            update_fields = []
            if "track_inventory" in cleaned_input:
                variant.track_inventory = cleaned_input["track_inventory"]
                update_fields.append("track_inventory")
            if "sku" in cleaned_input:
                variant.sku = cleaned_input["sku"]
                update_fields.append("sku")
            if update_fields:
                variant.save(update_fields=update_fields)
        # Recalculate the "minimal variant price"
        update_product_minimal_variant_price_task.delay(instance.pk)

        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)


class ProductDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product to delete.")

    class Meta:
        description = "Deletes a product."
        model = models.Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        model = models.Product
        description = "Update public metadata for product."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = True
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductClearMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears public metadata item for product."
        model = models.Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = True
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Update private metadata for product."
        model = models.Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = False
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears private metadata item for product."
        model = models.Product
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = False
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductVariantInput(graphene.InputObjectType):
    attributes = graphene.List(
        AttributeValueInput,
        required=False,
        description="List of attributes specific to this variant.",
    )
    cost_price = Decimal(description="Cost price of the variant.")
    price_override = Decimal(description="Special price of the particular variant.")
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
        cls, attributes, used_attribute_values, instance=None
    ):
        attribute_values = defaultdict(list)
        for attribute in attributes:
            attribute_values[attribute.id].extend(attribute.values)
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

        if "cost_price" in cleaned_input:
            cost_price = cleaned_input.pop("cost_price")
            if cost_price and cost_price < 0:
                raise ValidationError(
                    {
                        "costPrice": ValidationError(
                            "Product price cannot be lower than 0.",
                            code=ProductErrorCode.INVALID.value,
                        )
                    }
                )
            cleaned_input["cost_price_amount"] = cost_price

        if "price_override" in cleaned_input:
            price_override = cleaned_input.pop("price_override")
            if price_override and price_override < 0:
                raise ValidationError(
                    {
                        "priceOverride": ValidationError(
                            "Product price cannot be lower than 0.",
                            code=ProductErrorCode.INVALID.value,
                        )
                    }
                )
            cleaned_input["price_override_amount"] = price_override

        stocks = cleaned_input.get("stocks")
        if stocks:
            cls.check_for_duplicates_in_stocks(stocks)

        # Attributes are provided as list of `AttributeValueInput` objects.
        # We need to transform them into the format they're stored in the
        # `Product` model, which is HStore field that maps attribute's PK to
        # the value's PK.
        attributes = cleaned_input.get("attributes")
        if attributes:
            if instance.product_id is not None:
                # If the variant is getting updated,
                # simply retrieve the associated product type
                product_type = instance.product.product_type
                used_attribute_values = get_used_variants_attribute_values(
                    instance.product
                )
            else:
                # If the variant is getting created, no product type is associated yet,
                # retrieve it from the required "product" input field
                product_type = cleaned_input["product"].product_type
                used_attribute_values = get_used_variants_attribute_values(
                    cleaned_input["product"]
                )

            try:
                cls.validate_duplicated_attribute_values(
                    attributes, used_attribute_values, instance
                )
                cleaned_input["attributes"] = cls.clean_attributes(
                    attributes, product_type
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
                {"stocks": ValidationError(error_msg, code=ProductErrorCode.UNIQUE)}
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
        # Recalculate the "minimal variant price" for the parent product
        update_product_minimal_variant_price_task.delay(instance.product_id)
        stocks = cleaned_input.get("stocks")
        if stocks:
            cls.create_variant_stocks(instance, stocks)

        attributes = cleaned_input.get("attributes")
        if attributes:
            AttributeAssignmentMixin.save(instance, attributes)
            instance.name = generate_name_for_variant(instance)
            instance.save(update_fields=["name"])

    @classmethod
    def create_variant_stocks(cls, variant, stocks):
        warehouse_ids = [stock["warehouse"] for stock in stocks]
        warehouses = cls.get_nodes_or_error(
            warehouse_ids, "warehouse", only_type=Warehouse
        )
        create_stocks(variant, stocks, warehouses)


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

    @classmethod
    def validate_duplicated_attribute_values(
        cls, attributes, used_attribute_values, instance=None
    ):
        # Check if the variant is getting updated,
        # and the assigned attributes do not change
        if instance.product_id is not None:
            assigned_attributes = get_used_attribute_values_for_variant(instance)
            input_attribute_values = defaultdict(list)
            for attribute in attributes:
                input_attribute_values[attribute.id].extend(attribute.values)
            if input_attribute_values == assigned_attributes:
                return
        # if assigned attributes is getting updated run duplicated attribute validation
        super().validate_duplicated_attribute_values(attributes, used_attribute_values)


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
        # Update the "minimal_variant_prices" of the parent product
        update_product_minimal_variant_price_task.delay(instance.product_id)
        return super().success_response(instance)


class ProductVariantUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        model = models.ProductVariant
        description = "Update public metadata for product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = True
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductVariantClearMeta(ClearMetaBaseMutation):
    class Meta:
        model = models.ProductVariant
        description = "Clears public metadata for product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = True
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductVariantUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        model = models.ProductVariant
        description = "Update private metadata for product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = False
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductVariantClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        model = models.ProductVariant
        description = "Clears private metadata for product variant."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = False
        error_type_class = ProductError
        error_type_field = "product_errors"


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
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
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

        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        if "product_attributes" in cleaned_data:
            instance.product_attributes.set(cleaned_data["product_attributes"])
        if "variant_attributes" in cleaned_data:
            instance.variant_attributes.set(cleaned_data["variant_attributes"])


class ProductTypeUpdate(ProductTypeCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product type to update.")
        input = ProductTypeInput(
            required=True, description="Fields required to update a product type."
        )

    class Meta:
        description = "Updates an existing product type."
        model = models.ProductType
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
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
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductTypeUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        model = models.ProductType
        description = "Update public metadata for product type."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = True
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductTypeClearMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears public metadata for product type."
        model = models.ProductType
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = True
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductTypeUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Update private metadata for product type."
        model = models.ProductType
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = False
        error_type_class = ProductError
        error_type_field = "product_errors"


class ProductTypeClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears private metadata for product type."
        model = models.ProductType
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = False
        error_type_class = ProductError
        error_type_field = "product_errors"


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

        return ProductImageReorder(product=product, images=images)


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
        return ProductImageDelete(product=image.product, image=image)


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

        return VariantImageUnassign(product_variant=variant, image=image)
