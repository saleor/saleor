from collections import defaultdict
from typing import TYPE_CHECKING, List

import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify

from ....attribute import AttributeInputType, AttributeType, models as attribute_models
from ....attribute.error_codes import AttributeErrorCode
from ....core.exceptions import PermissionDenied
from ....core.permissions import (
    PageTypePermissions,
    ProductPermissions,
    ProductTypePermissions,
)
from ....product import models
from ....product.error_codes import ProductErrorCode
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.types.common import AttributeError, ProductError
from ...core.utils import (
    from_global_id_strict_type,
    validate_slug_and_generate_if_needed,
)
from ...core.utils.reordering import perform_reordering
from ...meta.deprecated.mutations import ClearMetaBaseMutation, UpdateMetaBaseMutation
from ...product.types import ProductType
from ...utils import resolve_global_ids_to_primary_keys
from ..descriptions import AttributeDescriptions, AttributeValueDescriptions
from ..enums import AttributeInputTypeEnum, AttributeTypeEnum, ProductAttributeType
from ..types import Attribute, AttributeValue
from .common import ReorderInput

if TYPE_CHECKING:
    from django.db.models import QuerySet


class AttributeValueCreateInput(graphene.InputObjectType):
    name = graphene.String(required=True, description=AttributeValueDescriptions.NAME)


class AttributeCreateInput(graphene.InputObjectType):
    input_type = AttributeInputTypeEnum(description=AttributeDescriptions.INPUT_TYPE)
    name = graphene.String(required=True, description=AttributeDescriptions.NAME)
    slug = graphene.String(required=False, description=AttributeDescriptions.SLUG)
    type = AttributeTypeEnum(description=AttributeDescriptions.TYPE, required=True)
    values = graphene.List(
        AttributeValueCreateInput, description=AttributeDescriptions.VALUES
    )
    value_required = graphene.Boolean(description=AttributeDescriptions.VALUE_REQUIRED)
    is_variant_only = graphene.Boolean(
        required=False, description=AttributeDescriptions.IS_VARIANT_ONLY
    )
    visible_in_storefront = graphene.Boolean(
        description=AttributeDescriptions.VISIBLE_IN_STOREFRONT
    )
    filterable_in_storefront = graphene.Boolean(
        description=AttributeDescriptions.FILTERABLE_IN_STOREFRONT
    )
    filterable_in_dashboard = graphene.Boolean(
        description=AttributeDescriptions.FILTERABLE_IN_DASHBOARD
    )
    storefront_search_position = graphene.Int(
        required=False, description=AttributeDescriptions.STOREFRONT_SEARCH_POSITION
    )
    available_in_grid = graphene.Boolean(
        required=False, description=AttributeDescriptions.AVAILABLE_IN_GRID
    )


class AttributeUpdateInput(graphene.InputObjectType):
    name = graphene.String(description=AttributeDescriptions.NAME)
    slug = graphene.String(description=AttributeDescriptions.SLUG)
    remove_values = graphene.List(
        graphene.ID,
        name="removeValues",
        description="IDs of values to be removed from this attribute.",
    )
    add_values = graphene.List(
        AttributeValueCreateInput,
        name="addValues",
        description="New values to be created for this attribute.",
    )
    value_required = graphene.Boolean(description=AttributeDescriptions.VALUE_REQUIRED)
    is_variant_only = graphene.Boolean(
        required=False, description=AttributeDescriptions.IS_VARIANT_ONLY
    )
    visible_in_storefront = graphene.Boolean(
        description=AttributeDescriptions.VISIBLE_IN_STOREFRONT
    )
    filterable_in_storefront = graphene.Boolean(
        description=AttributeDescriptions.FILTERABLE_IN_STOREFRONT
    )
    filterable_in_dashboard = graphene.Boolean(
        description=AttributeDescriptions.FILTERABLE_IN_DASHBOARD
    )
    storefront_search_position = graphene.Int(
        required=False, description=AttributeDescriptions.STOREFRONT_SEARCH_POSITION
    )
    available_in_grid = graphene.Boolean(
        required=False, description=AttributeDescriptions.AVAILABLE_IN_GRID
    )


class ProductAttributeAssignInput(graphene.InputObjectType):
    id = graphene.ID(required=True, description="The ID of the attribute to assign.")
    type = ProductAttributeType(
        required=True, description="The attribute type to be assigned as."
    )


class AttributeMixin:
    @classmethod
    def check_values_are_unique(cls, values_input, attribute):
        # Check values uniqueness in case of creating new attribute.
        existing_values = attribute.values.values_list("slug", flat=True)
        for value_data in values_input:
            slug = slugify(value_data["name"], allow_unicode=True)
            if slug in existing_values:
                msg = (
                    "Value %s already exists within this attribute."
                    % value_data["name"]
                )
                raise ValidationError(
                    {
                        cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                            msg, code=AttributeErrorCode.ALREADY_EXISTS
                        )
                    }
                )

        new_slugs = [
            slugify(value_data["name"], allow_unicode=True)
            for value_data in values_input
        ]
        if len(set(new_slugs)) != len(new_slugs):
            raise ValidationError(
                {
                    cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                        "Provided values are not unique.",
                        code=AttributeErrorCode.UNIQUE,
                    )
                }
            )

    @classmethod
    def clean_values(cls, cleaned_input, attribute):
        """Clean attribute values.

        Transforms AttributeValueCreateInput into AttributeValue instances.
        Slugs are created from given names and checked for uniqueness within
        an attribute.
        """
        values_input = cleaned_input.get(cls.ATTRIBUTE_VALUES_FIELD)

        if values_input is None:
            return

        for value_data in values_input:
            value_data["slug"] = slugify(value_data["name"], allow_unicode=True)
            attribute_value = attribute_models.AttributeValue(
                **value_data, attribute=attribute
            )
            try:
                attribute_value.full_clean()
            except ValidationError as validation_errors:
                for field, err in validation_errors.error_dict.items():
                    if field == "attribute":
                        continue
                    raise ValidationError({cls.ATTRIBUTE_VALUES_FIELD: err})
        cls.check_values_are_unique(values_input, attribute)

    @classmethod
    def clean_attribute(cls, instance, cleaned_input):
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = AttributeErrorCode.REQUIRED.value
            raise ValidationError({"slug": error})

        return cleaned_input

    @classmethod
    def _save_m2m(cls, info, attribute, cleaned_data):
        super()._save_m2m(info, attribute, cleaned_data)
        values = cleaned_data.get(cls.ATTRIBUTE_VALUES_FIELD) or []
        for value in values:
            attribute.values.create(**value)


class AttributeCreate(AttributeMixin, ModelMutation):
    # Needed by AttributeMixin,
    # represents the input name for the passed list of values
    ATTRIBUTE_VALUES_FIELD = "values"

    attribute = graphene.Field(Attribute, description="The created attribute.")

    class Arguments:
        input = AttributeCreateInput(
            required=True, description="Fields required to create an attribute."
        )

    class Meta:
        model = attribute_models.Attribute
        description = "Creates an attribute."
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        input = data.get("input")
        # check permissions based on attribute type
        if input["type"] == AttributeTypeEnum.PRODUCT_TYPE.value:
            permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        else:
            permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        if not cls.check_permissions(info.context, permissions):
            raise PermissionDenied()

        instance = attribute_models.Attribute()

        # Do cleaning and uniqueness checks
        cleaned_input = cls.clean_input(info, instance, input)
        cls.clean_attribute(instance, cleaned_input)
        cls.clean_values(cleaned_input, instance)

        # Construct the attribute
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)

        # Commit it
        instance.save()
        cls._save_m2m(info, instance, cleaned_input)

        # Return the attribute that was created
        return AttributeCreate(attribute=instance)


class AttributeUpdate(AttributeMixin, ModelMutation):
    # Needed by AttributeMixin,
    # represents the input name for the passed list of values
    ATTRIBUTE_VALUES_FIELD = "add_values"

    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of an attribute to update.")
        input = AttributeUpdateInput(
            required=True, description="Fields required to update an attribute."
        )

    class Meta:
        model = attribute_models.Attribute
        description = "Updates attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def clean_remove_values(cls, cleaned_input, instance):
        """Check if the values to be removed are assigned to the given attribute."""
        remove_values = cleaned_input.get("remove_values", [])
        for value in remove_values:
            if value.attribute != instance:
                msg = "Value %s does not belong to this attribute." % value
                raise ValidationError(
                    {
                        "remove_values": ValidationError(
                            msg, code=AttributeErrorCode.INVALID
                        )
                    }
                )
        return remove_values

    @classmethod
    def _save_m2m(cls, info, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        for attribute_value in cleaned_data.get("remove_values", []):
            attribute_value.delete()

    @classmethod
    def perform_mutation(cls, _root, info, id, input):
        instance = cls.get_node_or_error(info, id, only_type=Attribute)

        # Do cleaning and uniqueness checks
        cleaned_input = cls.clean_input(info, instance, input)
        cls.clean_attribute(instance, cleaned_input)
        cls.clean_values(cleaned_input, instance)
        cls.clean_remove_values(cleaned_input, instance)

        # Construct the attribute
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)

        # Commit it
        instance.save()
        cls._save_m2m(info, instance, cleaned_input)

        # Return the attribute that was created
        return AttributeUpdate(attribute=instance)


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

        # check if attributes' input type is assignable to variants
        not_assignable_to_variant = attribute_models.Attribute.objects.filter(
            Q(pk__in=variant_attrs_pks)
            & Q(input_type__in=AttributeInputType.NON_ASSIGNABLE_TO_VARIANTS)
        )

        if not_assignable_to_variant:
            not_assignable_attr_ids = [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in not_assignable_to_variant
            ]
            error = ValidationError(
                (
                    f"Attributes having for input types "
                    f"{AttributeInputType.NON_ASSIGNABLE_TO_VARIANTS} "
                    f"cannot be assigned as variant attributes"
                ),
                code=ProductErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED,
                params={"attributes": not_assignable_attr_ids},
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


class AttributeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an attribute to delete.")

    class Meta:
        model = attribute_models.Attribute
        description = "Deletes an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"


class AttributeUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        model = attribute_models.Attribute
        description = "Update public metadata for attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        public = True
        error_type_class = AttributeError
        error_type_field = "attribute_errors"


class AttributeClearMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears public metadata item for attribute."
        model = attribute_models.Attribute
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        public = True
        error_type_class = AttributeError
        error_type_field = "attribute_errors"


class AttributeUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Update public metadata for attribute."
        model = attribute_models.Attribute
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        public = False
        error_type_class = AttributeError
        error_type_field = "attribute_errors"


class AttributeClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears public metadata item for attribute."
        model = attribute_models.Attribute
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        public = False
        error_type_class = AttributeError
        error_type_field = "attribute_errors"


def validate_value_is_unique(
    attribute: attribute_models.Attribute, value: attribute_models.AttributeValue
):
    """Check if the attribute value is unique within the attribute it belongs to."""
    duplicated_values = attribute.values.exclude(pk=value.pk).filter(slug=value.slug)
    if duplicated_values.exists():
        raise ValidationError(
            {
                "name": ValidationError(
                    f"Value with slug {value.slug} already exists.",
                    code=AttributeErrorCode.ALREADY_EXISTS.value,
                )
            }
        )


class AttributeValueCreate(ModelMutation):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        attribute_id = graphene.ID(
            required=True,
            name="attribute",
            description="Attribute to which value will be assigned.",
        )
        input = AttributeValueCreateInput(
            required=True, description="Fields required to create an AttributeValue."
        )

    class Meta:
        model = attribute_models.AttributeValue
        description = "Creates a value for an attribute."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        cleaned_input["slug"] = slugify(cleaned_input["name"], allow_unicode=True)
        return cleaned_input

    @classmethod
    def clean_instance(cls, info, instance):
        validate_value_is_unique(instance.attribute, instance)
        super().clean_instance(info, instance)

    @classmethod
    def perform_mutation(cls, _root, info, attribute_id, input):
        attribute = cls.get_node_or_error(info, attribute_id, only_type=Attribute)
        instance = attribute_models.AttributeValue(attribute=attribute)
        cleaned_input = cls.clean_input(info, instance, input)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)

        instance.save()
        cls._save_m2m(info, instance, cleaned_input)
        return AttributeValueCreate(attribute=attribute, attributeValue=instance)


class AttributeValueUpdate(ModelMutation):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of an AttributeValue to update."
        )
        input = AttributeValueCreateInput(
            required=True, description="Fields required to update an AttributeValue."
        )

    class Meta:
        model = attribute_models.AttributeValue
        description = "Updates value of an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        if "name" in cleaned_input:
            cleaned_input["slug"] = slugify(cleaned_input["name"], allow_unicode=True)
        return cleaned_input

    @classmethod
    def clean_instance(cls, info, instance):
        validate_value_is_unique(instance.attribute, instance)
        super().clean_instance(info, instance)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response


class AttributeValueDelete(ModelDeleteMutation):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of a value to delete.")

    class Meta:
        model = attribute_models.AttributeValue
        description = "Deletes a value of an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response


class BaseReorderAttributesMutation(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def prepare_operations(cls, moves: ReorderInput, attributes: "QuerySet"):
        """Prepare operations dict for reordering attributes.

        Operation dict format:
            key: attribute pk,
            value: sort_order value - relative sorting position of the attribute
        """
        attribute_ids = []
        sort_orders = []

        # resolve attribute moves
        for move_info in moves:
            attribute_ids.append(move_info.id)
            sort_orders.append(move_info.sort_order)

        _, attr_pks = resolve_global_ids_to_primary_keys(attribute_ids, Attribute)
        attr_pks = [int(pk) for pk in attr_pks]

        attributes_m2m = attributes.filter(attribute_id__in=attr_pks)

        if attributes_m2m.count() != len(attr_pks):
            attribute_pks = attributes_m2m.values_list("attribute_id", flat=True)
            invalid_attrs = set(attr_pks) - set(attribute_pks)
            invalid_attr_ids = [
                graphene.Node.to_global_id("Attribute", attr_pk)
                for attr_pk in invalid_attrs
            ]
            raise ValidationError(
                "Couldn't resolve to an attribute.",
                params={"attributes": invalid_attr_ids},
            )

        attributes_m2m = list(attributes_m2m)
        attributes_m2m.sort(
            key=lambda e: attr_pks.index(e.attribute.pk)
        )  # preserve order in pks

        operations = {
            attribute.pk: sort_order
            for attribute, sort_order in zip(attributes_m2m, sort_orders)
        }

        return operations


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


class AttributeReorderValues(BaseMutation):
    attribute = graphene.Field(
        Attribute, description="Attribute from which values are reordered."
    )

    class Meta:
        description = "Reorder the values of an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    class Arguments:
        attribute_id = graphene.Argument(
            graphene.ID, required=True, description="ID of an attribute."
        )
        moves = graphene.List(
            ReorderInput,
            required=True,
            description="The list of reordering operations for given attribute values.",
        )

    @classmethod
    def perform_mutation(cls, _root, info, attribute_id, moves):
        pk = from_global_id_strict_type(
            attribute_id, only_type=Attribute, field="attribute_id"
        )

        try:
            attribute = attribute_models.Attribute.objects.prefetch_related(
                "values"
            ).get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "attribute_id": ValidationError(
                        f"Couldn't resolve to an attribute: {attribute_id}",
                        code=AttributeErrorCode.NOT_FOUND,
                    )
                }
            )

        values_m2m = attribute.values
        operations = {}

        # Resolve the values
        for move_info in moves:
            value_pk = from_global_id_strict_type(
                move_info.id, only_type=AttributeValue, field="moves"
            )

            try:
                m2m_info = values_m2m.get(pk=int(value_pk))
            except ObjectDoesNotExist:
                raise ValidationError(
                    {
                        "moves": ValidationError(
                            f"Couldn't resolve to an attribute value: {move_info.id}",
                            code=AttributeErrorCode.NOT_FOUND,
                        )
                    }
                )
            operations[m2m_info.pk] = move_info.sort_order

        with transaction.atomic():
            perform_reordering(values_m2m, operations)
        attribute.refresh_from_db(fields=["values"])
        return AttributeReorderValues(attribute=attribute)
