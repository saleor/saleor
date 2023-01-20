import graphene
from django.core.exceptions import ValidationError

from .....attribute import AttributeType
from .....permission.enums import ProductTypePermissions
from .....product import ProductTypeKind, models
from .....product.error_codes import ProductErrorCode
from ....core import ResolveInfo
from ....core.descriptions import DEPRECATED_IN_3X_INPUT
from ....core.mutations import ModelMutation
from ....core.scalars import WeightScalar
from ....core.types import NonNullList, ProductError
from ....core.validators import validate_slug_and_generate_if_needed
from ...enums import ProductTypeKindEnum
from ...types import ProductType


class ProductTypeInput(graphene.InputObjectType):
    name = graphene.String(description="Name of the product type.")
    slug = graphene.String(description="Product type slug.")
    kind = ProductTypeKindEnum(description="The product type kind.")
    has_variants = graphene.Boolean(
        description=(
            "Determines if product of this type has multiple variants. This option "
            "mainly simplifies product management in the dashboard. There is always at "
            "least one variant created under the hood."
        )
    )
    product_attributes = NonNullList(
        graphene.ID,
        description="List of attributes shared among all product variants.",
        name="productAttributes",
    )
    variant_attributes = NonNullList(
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
    tax_code = graphene.String(
        description=(
            f"Tax rate for enabled tax gateway. {DEPRECATED_IN_3X_INPUT}. "
            "Use tax classes to control the tax calculation for a product type."
        )
    )
    tax_class = graphene.ID(
        description=(
            "ID of a tax class to assign to this product type. All products of this "
            "product type would use this tax class, unless it's overridden in the "
            "`Product` type."
        ),
        required=False,
    )


class ProductTypeCreate(ModelMutation):
    class Arguments:
        input = ProductTypeInput(
            required=True, description="Fields required to create a product type."
        )

    class Meta:
        description = "Creates a new product type."
        model = models.ProductType
        object_type = ProductType
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def clean_product_kind(cls, _instance, data):
        # Fallback to ProductTypeKind.NORMAL if kind is not provided in the input.
        # This method can be dropped when we separate inputs for `productTypeCreate`
        # and `productTypeUpdate` - now they reuse the input class and all fields are
        # optional, while `kind` is required in the model.
        return data.get("kind") or ProductTypeKind.NORMAL

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        cleaned_input["kind"] = cls.clean_product_kind(instance, cleaned_input)

        weight = cleaned_input.get("weight")
        if weight and weight.value < 0:
            raise ValidationError(
                {
                    "weight": ValidationError(
                        "Product type can't have negative weight.",
                        code=ProductErrorCode.INVALID.value,
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
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        product_attributes = cleaned_data.get("product_attributes")
        variant_attributes = cleaned_data.get("variant_attributes")
        if product_attributes is not None:
            instance.product_attributes.set(product_attributes)
        if variant_attributes is not None:
            instance.variant_attributes.set(variant_attributes)
