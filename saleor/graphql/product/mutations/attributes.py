from collections import defaultdict
from typing import List

import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Q

from ....attribute import AttributeType
from ....attribute import models as attribute_models
from ....core.permissions import ProductPermissions, ProductTypePermissions
from ....product import models
from ....product.error_codes import ProductErrorCode
from ...attribute.mutations import (
    BaseReorderAttributesMutation,
    BaseReorderAttributeValuesMutation,
)
from ...attribute.types import Attribute
from ...channel import ChannelContext
from ...core.inputs import ReorderInput
from ...core.mutations import BaseMutation
from ...core.types.common import ProductError
from ...core.utils import from_global_id_strict_type
from ...core.utils.reordering import perform_reordering
from ...product.types import Product, ProductType, ProductVariant
from ..enums import ProductAttributeType


class ProductAttributeAssignInput(graphene.InputObjectType):
    id = graphene.ID(required=True, description="The ID of the attribute to assign.")
    type = ProductAttributeType(
        required=True, description="The attribute type to be assigned as."
    )


class ProductAttributeAssign(BaseMutation):
    product_type = graphene.Field(ProductType, description="The updated product type.")

    class Arguments:
        product_type_id = graphene.ID(
            required=True,
            description="ID of the product type to assign the attributes into.",
        )
        operations = graphene.List(
            ProductAttributeAssignInput,
            required=True,
            description="The operations to perform.",
        )

    class Meta:
        description = "Assign attributes to a given product type."
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.has_perm(
            ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES
        )

    @classmethod
    def get_operations(cls, info, operations: List[ProductAttributeAssignInput]):
        """Resolve all passed global ids into integer PKs of the Attribute type."""
        product_attrs_pks = []
        variant_attrs_pks = []

        for operation in operations:
            pk = from_global_id_strict_type(
                operation.id, only_type=Attribute, field="operations"
            )
            if operation.type == ProductAttributeType.PRODUCT:
                product_attrs_pks.append(pk)
            else:
                variant_attrs_pks.append(pk)

        return product_attrs_pks, variant_attrs_pks

    @classmethod
    def check_attributes_types(cls, errors, product_attrs_pks, variant_attrs_pks):
        """Ensure the attributes are product attributes."""

        not_valid_attributes = attribute_models.Attribute.objects.filter(
            Q(pk__in=product_attrs_pks) | Q(pk__in=variant_attrs_pks)
        ).exclude(type=AttributeType.PRODUCT_TYPE)

        if not_valid_attributes:
            not_valid_attr_ids = [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in not_valid_attributes
            ]
            error = ValidationError(
                "Only product attributes can be assigned.",
                code=ProductErrorCode.INVALID.value,
                params={"attributes": not_valid_attr_ids},
            )
            errors["operations"].append(error)

    @classmethod
    def check_operations_not_assigned_already(
        cls, errors, product_type, product_attrs_pks, variant_attrs_pks
    ):
        qs = (
            attribute_models.Attribute.objects.get_assigned_product_type_attributes(
                product_type.pk
            )
            .values_list("pk", "name", "slug")
            .filter(Q(pk__in=product_attrs_pks) | Q(pk__in=variant_attrs_pks))
        )

        invalid_attributes = list(qs)
        if invalid_attributes:
            msg = ", ".join(
                [f"{name} ({slug})" for _, name, slug in invalid_attributes]
            )
            invalid_attr_ids = [
                graphene.Node.to_global_id("Attribute", attr[0])
                for attr in invalid_attributes
            ]
            error = ValidationError(
                (f"{msg} have already been assigned to this product type."),
                code=ProductErrorCode.ATTRIBUTE_ALREADY_ASSIGNED,
                params={"attributes": invalid_attr_ids},
            )
            errors["operations"].append(error)

    @classmethod
    def check_product_operations_are_assignable(cls, errors, product_attrs_pks):
        restricted_attributes = attribute_models.Attribute.objects.filter(
            pk__in=product_attrs_pks, is_variant_only=True
        )

        if restricted_attributes:
            restricted_attr_ids = [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in restricted_attributes
            ]
            error = ValidationError(
                "Cannot assign variant only attributes.",
                code=ProductErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED,
                params={"attributes": restricted_attr_ids},
            )
            errors["operations"].append(error)

    @classmethod
    def clean_operations(cls, product_type, product_attrs_pks, variant_attrs_pks):
        """Ensure the attributes are not already assigned to the product type."""
        errors = defaultdict(list)

        attrs_pk = product_attrs_pks + variant_attrs_pks
        attributes = attribute_models.Attribute.objects.filter(
            id__in=attrs_pk
        ).values_list("pk", flat=True)
        if len(attrs_pk) != len(attributes):
            invalid_attrs = set(attrs_pk) - set(attributes)
            invalid_attrs = [
                graphene.Node.to_global_id("Attribute", pk) for pk in invalid_attrs
            ]
            error = ValidationError(
                "Attribute doesn't exist.",
                code=ProductErrorCode.NOT_FOUND,
                params={"attributes": list(invalid_attrs)},
            )
            errors["operations"].append(error)

        cls.check_attributes_types(errors, product_attrs_pks, variant_attrs_pks)
        cls.check_product_operations_are_assignable(errors, product_attrs_pks)
        cls.check_operations_not_assigned_already(
            errors, product_type, product_attrs_pks, variant_attrs_pks
        )

        if errors:
            raise ValidationError(errors)

    @classmethod
    def save_field_values(cls, product_type, model_name, pks):
        """Add in bulk the PKs to assign to a given product type."""
        model = getattr(attribute_models, model_name)
        for pk in pks:
            model.objects.create(product_type=product_type, attribute_id=pk)

    @classmethod
    @transaction.atomic()
    def perform_mutation(cls, _root, info, **data):
        product_type_id: str = data["product_type_id"]
        operations: List[ProductAttributeAssignInput] = data["operations"]
        # Retrieve the requested product type
        product_type: models.ProductType = graphene.Node.get_node_from_global_id(
            info, product_type_id, only_type=ProductType
        )

        # Resolve all the passed IDs to ints
        product_attrs_pks, variant_attrs_pks = cls.get_operations(info, operations)

        if variant_attrs_pks and not product_type.has_variants:
            raise ValidationError(
                {
                    "operations": ValidationError(
                        "Variants are disabled in this product type.",
                        code=ProductErrorCode.ATTRIBUTE_VARIANTS_DISABLED.value,
                    )
                }
            )

        # Ensure the attribute are assignable
        cls.clean_operations(product_type, product_attrs_pks, variant_attrs_pks)

        # Commit
        cls.save_field_values(product_type, "AttributeProduct", product_attrs_pks)
        cls.save_field_values(product_type, "AttributeVariant", variant_attrs_pks)

        return cls(product_type=product_type)


class ProductAttributeUnassign(BaseMutation):
    product_type = graphene.Field(ProductType, description="The updated product type.")

    class Arguments:
        product_type_id = graphene.ID(
            required=True,
            description=(
                "ID of the product type from which the attributes should be unassigned."
            ),
        )
        attribute_ids = graphene.List(
            graphene.ID,
            required=True,
            description="The IDs of the attributes to unassign.",
        )

    class Meta:
        description = "Un-assign attributes from a given product type."
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.has_perm(
            ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES
        )

    @classmethod
    def save_field_values(cls, product_type, field, pks):
        """Add in bulk the PKs to assign to a given product type."""
        getattr(product_type, field).remove(*pks)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        product_type_id: str = data["product_type_id"]
        attribute_ids: List[str] = data["attribute_ids"]
        # Retrieve the requested product type
        product_type = graphene.Node.get_node_from_global_id(
            info, product_type_id, only_type=ProductType
        )  # type: models.ProductType

        # Resolve all the passed IDs to ints
        attribute_pks = [
            from_global_id_strict_type(
                attribute_id, only_type=Attribute, field="attribute_id"
            )
            for attribute_id in attribute_ids
        ]

        # Commit
        cls.save_field_values(product_type, "product_attributes", attribute_pks)
        cls.save_field_values(product_type, "variant_attributes", attribute_pks)

        return cls(product_type=product_type)


class ProductTypeReorderAttributes(BaseReorderAttributesMutation):
    product_type = graphene.Field(
        ProductType, description="Product type from which attributes are reordered."
    )

    class Meta:
        description = "Reorder the attributes of a product type."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    class Arguments:
        product_type_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a product type."
        )
        type = ProductAttributeType(
            required=True, description="The attribute type to reorder."
        )
        moves = graphene.List(
            ReorderInput,
            required=True,
            description="The list of attribute reordering operations.",
        )

    @classmethod
    def perform_mutation(cls, _root, info, product_type_id, type, moves):
        pk = from_global_id_strict_type(
            product_type_id, only_type=ProductType, field="product_type_id"
        )

        if type == ProductAttributeType.PRODUCT:
            m2m_field = "attributeproduct"
        else:
            m2m_field = "attributevariant"

        try:
            product_type = models.ProductType.objects.prefetch_related(m2m_field).get(
                pk=pk
            )
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "product_type_id": ValidationError(
                        (f"Couldn't resolve to a product type: {product_type_id}"),
                        code=ProductErrorCode.NOT_FOUND,
                    )
                }
            )

        attributes_m2m = getattr(product_type, m2m_field)

        try:
            operations = cls.prepare_operations(moves, attributes_m2m)
        except ValidationError as error:
            error.code = ProductErrorCode.NOT_FOUND.value
            raise ValidationError({"moves": error})

        with transaction.atomic():
            perform_reordering(attributes_m2m, operations)

        return ProductTypeReorderAttributes(product_type=product_type)


class ProductReorderAttributeValues(BaseReorderAttributeValuesMutation):
    product = graphene.Field(
        Product, description="Product from which attribute values are reordered."
    )

    class Meta:
        description = "Reorder product attribute values."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    class Arguments:
        product_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a product."
        )
        attribute_id = graphene.Argument(
            graphene.ID, required=True, description="ID of an attribute."
        )
        moves = graphene.List(
            ReorderInput,
            required=True,
            description="The list of reordering operations for given attribute values.",
        )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        product_id = data["product_id"]
        product = cls.perform(
            product_id, "product", data, "productvalueassignment", ProductErrorCode
        )

        return ProductReorderAttributeValues(
            product=ChannelContext(node=product, channel_slug=None)
        )

    @staticmethod
    def get_instance(instance_id: str):
        pk = from_global_id_strict_type(
            instance_id, only_type=Product, field="product_id"
        )

        try:
            product = models.Product.objects.prefetch_related("attributes").get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "product_id": ValidationError(
                        (f"Couldn't resolve to a product: {instance_id}"),
                        code=ProductErrorCode.NOT_FOUND.value,
                    )
                }
            )
        return product


class ProductVariantReorderAttributeValues(BaseReorderAttributeValuesMutation):
    product_variant = graphene.Field(
        ProductVariant,
        description="Product variant from which attribute values are reordered.",
    )

    class Meta:
        description = "Reorder product variant attribute values."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    class Arguments:
        variant_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a product variant."
        )
        attribute_id = graphene.Argument(
            graphene.ID, required=True, description="ID of an attribute."
        )
        moves = graphene.List(
            ReorderInput,
            required=True,
            description="The list of reordering operations for given attribute values.",
        )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        variant_id = data["variant_id"]
        variant = cls.perform(
            variant_id, "variant", data, "variantvalueassignment", ProductErrorCode
        )

        return ProductVariantReorderAttributeValues(
            product_variant=ChannelContext(node=variant, channel_slug=None)
        )

    @staticmethod
    def get_instance(instance_id: str):
        pk = from_global_id_strict_type(
            instance_id, only_type=ProductVariant, field="variant_id"
        )

        try:
            variant = models.ProductVariant.objects.prefetch_related("attributes").get(
                pk=pk
            )
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "variant_id": ValidationError(
                        (f"Couldn't resolve to a product variant: {instance_id}"),
                        code=ProductErrorCode.NOT_FOUND.value,
                    )
                }
            )
        return variant
