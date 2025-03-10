import graphene
from django.core.exceptions import ValidationError

from .....attribute import models as attribute_models
from .....core.tracing import traced_atomic_transaction
from .....core.utils.editorjs import clean_editor_js
from .....permission.enums import ProductPermissions
from .....product import models
from .....product.error_codes import ProductErrorCode
from ....attribute.types import AttributeValueInput
from ....attribute.utils import AttrValuesInput, ProductAttributeAssignmentMixin
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.descriptions import (
    DEPRECATED_IN_3X_INPUT,
    RICH_CONTENT,
)
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.fields import JSONString
from ....core.mutations import DeprecatedModelMutation
from ....core.scalars import WeightScalar
from ....core.types import BaseInputObjectType, NonNullList, ProductError, SeoInput
from ....core.validators import clean_seo_fields, validate_slug_and_generate_if_needed
from ....meta.inputs import MetadataInput
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Product
from ..utils import clean_tax_code


class ProductInput(BaseInputObjectType):
    attributes = NonNullList(AttributeValueInput, description="List of attributes.")
    category = graphene.ID(description="ID of the product's category.", name="category")
    charge_taxes = graphene.Boolean(
        description=(
            "Determine if taxes are being charged for the product. "
            f"{DEPRECATED_IN_3X_INPUT} Use `Channel.taxConfiguration` to configure "
            "whether tax collection is enabled."
        )
    )
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
    tax_code = graphene.String(
        description=(
            f"Tax rate for enabled tax gateway. {DEPRECATED_IN_3X_INPUT} "
            "Use tax classes to control the tax calculation for a product. "
            "If taxCode is provided, Saleor will try to find a tax class with given "
            "code (codes are stored in metadata) and assign it. If no tax class is "
            "found, it would be created and assigned."
        )
    )
    seo = SeoInput(description="Search engine optimization fields.")
    weight = WeightScalar(description="Weight of the Product.", required=False)
    rating = graphene.Float(description="Defines the product rating value.")
    metadata = NonNullList(
        MetadataInput,
        description=("Fields required to update the product metadata."),
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

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class StockInput(BaseInputObjectType):
    warehouse = graphene.ID(
        required=True, description="Warehouse in which stock is located."
    )
    quantity = graphene.Int(
        required=True, description="Quantity of items available for sell."
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class StockUpdateInput(BaseInputObjectType):
    stock = graphene.ID(required=True, description="Stock.")
    quantity = graphene.Int(
        required=True, description="Quantity of items available for sell."
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


class ProductCreateInput(ProductInput):
    product_type = graphene.ID(
        description="ID of the type that product belongs to.",
        name="productType",
        required=True,
    )

    class Meta:
        doc_category = DOC_CATEGORY_PRODUCTS


T_INPUT_MAP = list[tuple[attribute_models.Attribute, AttrValuesInput]]


class ProductCreate(DeprecatedModelMutation):
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
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def clean_attributes(
        cls, attributes: dict, product_type: models.ProductType
    ) -> T_INPUT_MAP:
        attributes_qs = product_type.product_attributes.all()
        attributes = ProductAttributeAssignmentMixin.clean_input(
            attributes, attributes_qs
        )
        return attributes

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        if "description" in cleaned_input:
            description = cleaned_input["description"]
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
        except ValidationError as e:
            e.code = ProductErrorCode.REQUIRED.value
            raise ValidationError({"slug": e}) from e

        if attributes and product_type:
            try:
                cleaned_input["attributes"] = cls.clean_attributes(
                    attributes, product_type
                )
            except ValidationError as e:
                raise ValidationError({"attributes": e}) from e

        clean_tax_code(cleaned_input)

        clean_seo_fields(cleaned_input)
        return cleaned_input

    @classmethod
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        with traced_atomic_transaction():
            instance.search_index_dirty = True
            instance.save()
            attributes = cleaned_input.get("attributes")
            if attributes:
                ProductAttributeAssignmentMixin.save(instance, attributes)

    @classmethod
    def _save_m2m(cls, _info: ResolveInfo, instance, cleaned_data):
        collections = cleaned_data.get("collections", None)
        if collections is not None:
            instance.collections.set(collections)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, _cleaned_input):
        product = models.Product.objects.get(pk=instance.pk)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.product_created, product)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        response = super().perform_mutation(_root, info, **data)
        product = getattr(response, cls._meta.return_field_name)

        # Wrap product instance with ChannelContext in response
        setattr(
            response,
            cls._meta.return_field_name,
            ChannelContext(node=product, channel_slug=None),
        )
        return response
