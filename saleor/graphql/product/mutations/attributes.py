from typing import List

import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Q
from django.template.defaultfilters import slugify

from ....core.permissions import ProductPermissions
from ....product import AttributeInputType, models
from ....product.error_codes import ProductErrorCode
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.types.common import ProductAttributeError, ProductError
from ...core.utils import (
    from_global_id_strict_type,
    validate_slug_and_generate_if_needed,
)
from ...core.utils.reordering import perform_reordering
from ...meta.deprecated.mutations import ClearMetaBaseMutation, UpdateMetaBaseMutation
from ...product.types import ProductType
from ..descriptions import AttributeDescriptions, AttributeValueDescriptions
from ..enums import AttributeInputTypeEnum, AttributeTypeEnum
from ..types import Attribute, AttributeValue


class AttributeValueCreateInput(graphene.InputObjectType):
    name = graphene.String(required=True, description=AttributeValueDescriptions.NAME)


class AttributeCreateInput(graphene.InputObjectType):
    input_type = AttributeInputTypeEnum(description=AttributeDescriptions.INPUT_TYPE)
    name = graphene.String(required=True, description=AttributeDescriptions.NAME)
    slug = graphene.String(required=False, description=AttributeDescriptions.SLUG)
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


class AttributeAssignInput(graphene.InputObjectType):
    id = graphene.ID(required=True, description="The ID of the attribute to assign.")
    type = AttributeTypeEnum(
        required=True, description="The attribute type to be assigned as."
    )


class ReorderInput(graphene.InputObjectType):
    id = graphene.ID(required=True, description="The ID of the item to move.")
    sort_order = graphene.Int(
        description=(
            "The new relative sorting position of the item (from -inf to +inf)."
        )
    )


class AttributeMixin:
    @classmethod
    def check_values_are_unique(cls, values_input, attribute):
        # Check values uniqueness in case of creating new attribute.
        existing_values = attribute.values.values_list("slug", flat=True)
        for value_data in values_input:
            slug = slugify(value_data["name"])
            if slug in existing_values:
                msg = (
                    "Value %s already exists within this attribute."
                    % value_data["name"]
                )
                raise ValidationError(
                    {
                        cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                            msg, code=ProductErrorCode.ALREADY_EXISTS
                        )
                    }
                )

        new_slugs = [slugify(value_data["name"]) for value_data in values_input]
        if len(set(new_slugs)) != len(new_slugs):
            raise ValidationError(
                {
                    cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                        "Provided values are not unique.", code=ProductErrorCode.UNIQUE
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
            value_data["slug"] = slugify(value_data["name"])
            attribute_value = models.AttributeValue(**value_data, attribute=attribute)
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
            error.code = ProductErrorCode.REQUIRED.value
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
        model = models.Attribute
        description = "Creates an attribute."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = models.Attribute()

        # Do cleaning and uniqueness checks
        cleaned_input = cls.clean_input(info, instance, data.get("input"))
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
        model = models.Attribute
        description = "Updates attribute."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

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
                            msg, code=ProductErrorCode.INVALID
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


class AttributeAssign(BaseMutation):
    product_type = graphene.Field(ProductType, description="The updated product type.")

    class Arguments:
        product_type_id = graphene.ID(
            required=True,
            description="ID of the product type to assign the attributes into.",
        )
        operations = graphene.List(
            AttributeAssignInput,
            required=True,
            description="The operations to perform.",
        )

    class Meta:
        description = "Assign attributes to a given product type."
        error_type_class = ProductAttributeError
        error_type_field = "product_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.has_perm(ProductPermissions.MANAGE_PRODUCTS)

    @classmethod
    def get_operations(cls, info, operations: List[AttributeAssignInput]):
        """Resolve all passed global ids into integer PKs of the Attribute type."""
        product_attrs_pks = []
        variant_attrs_pks = []

        for operation in operations:
            pk = from_global_id_strict_type(
                operation.id, only_type=Attribute, field="operations"
            )
            if operation.type == AttributeTypeEnum.PRODUCT:
                product_attrs_pks.append(pk)
            else:
                variant_attrs_pks.append(pk)

        return product_attrs_pks, variant_attrs_pks

    @classmethod
    def check_operations_not_assigned_already(
        cls, product_type, product_attrs_pks, variant_attrs_pks
    ):
        qs = (
            models.Attribute.objects.get_assigned_attributes(product_type.pk)
            .values_list("name", "slug")
            .filter(Q(pk__in=product_attrs_pks) | Q(pk__in=variant_attrs_pks))
        )

        invalid_attributes = list(qs)
        if invalid_attributes:
            msg = ", ".join([f"{name} ({slug})" for name, slug in invalid_attributes])
            raise ValidationError(
                {
                    "operations": ValidationError(
                        (f"{msg} have already been assigned to this product type."),
                        code=ProductErrorCode.ATTRIBUTE_ALREADY_ASSIGNED,
                    )
                }
            )

        # check if attributes' input type is assignable to variants
        is_not_assignable_to_variant = models.Attribute.objects.filter(
            Q(pk__in=variant_attrs_pks)
            & Q(input_type__in=AttributeInputType.NON_ASSIGNABLE_TO_VARIANTS)
        ).exists()

        if is_not_assignable_to_variant:
            raise ValidationError(
                {
                    "operations": ValidationError(
                        (
                            f"Attributes having for input types "
                            f"{AttributeInputType.NON_ASSIGNABLE_TO_VARIANTS} "
                            f"cannot be assigned as variant attributes"
                        ),
                        code=ProductErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED,
                    )
                }
            )

    @classmethod
    def check_product_operations_are_assignable(cls, product_attrs_pks):
        contains_restricted_attributes = models.Attribute.objects.filter(
            pk__in=product_attrs_pks, is_variant_only=True
        ).exists()

        if contains_restricted_attributes:
            raise ValidationError(
                {
                    "operations": ValidationError(
                        "Cannot assign variant only attributes.",
                        code=ProductErrorCode.ATTRIBUTE_CANNOT_BE_ASSIGNED,
                    )
                }
            )

    @classmethod
    def clean_operations(cls, product_type, product_attrs_pks, variant_attrs_pks):
        """Ensure the attributes are not already assigned to the product type."""
        attrs_pk = product_attrs_pks + variant_attrs_pks
        attributes = models.Attribute.objects.filter(id__in=attrs_pk).values_list(
            "pk", flat=True
        )
        if len(attrs_pk) != len(attributes):
            invalid_attrs = set(attrs_pk) - set(attributes)
            invalid_attrs = [
                graphene.Node.to_global_id("Attribute", pk) for pk in invalid_attrs
            ]
            raise ValidationError(
                {
                    "operations": ValidationError(
                        f"Attribute doesn't exist.",
                        code=ProductErrorCode.NOT_FOUND,
                        params={"attributes": list(invalid_attrs)},
                    )
                }
            )
        cls.check_product_operations_are_assignable(product_attrs_pks)
        cls.check_operations_not_assigned_already(
            product_type, product_attrs_pks, variant_attrs_pks
        )

    @classmethod
    def save_field_values(cls, product_type, model_name, pks):
        """Add in bulk the PKs to assign to a given product type."""
        model = getattr(models, model_name)
        for pk in pks:
            model.objects.create(product_type=product_type, attribute_id=pk)

    @classmethod
    @transaction.atomic()
    def perform_mutation(cls, _root, info, **data):
        product_type_id: str = data["product_type_id"]
        operations: List[AttributeAssignInput] = data["operations"]
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


class AttributeUnassign(BaseMutation):
    product_type = graphene.Field(ProductType, description="The updated product type.")

    class Arguments:
        product_type_id = graphene.ID(
            required=True,
            description="ID of the product type to assign the attributes into.",
        )
        attribute_ids = graphene.List(
            graphene.ID,
            required=True,
            description="The IDs of the attributes to assign.",
        )

    class Meta:
        description = "Un-assign attributes from a given product type."
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def check_permissions(cls, context):
        return context.user.has_perm(ProductPermissions.MANAGE_PRODUCTS)

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
        model = models.Attribute
        description = "Deletes an attribute."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"


class AttributeUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        model = models.Attribute
        description = "Update public metadata for attribute."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = True
        error_type_class = ProductError
        error_type_field = "product_errors"


class AttributeClearMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears public metadata item for attribute."
        model = models.Attribute
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = True
        error_type_class = ProductError
        error_type_field = "product_errors"


class AttributeUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Update public metadata for attribute."
        model = models.Attribute
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = False
        error_type_class = ProductError
        error_type_field = "product_errors"


class AttributeClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears public metadata item for attribute."
        model = models.Attribute
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        public = False
        error_type_class = ProductError
        error_type_field = "product_errors"


def validate_value_is_unique(attribute: models.Attribute, value: models.AttributeValue):
    """Check if the attribute value is unique within the attribute it belongs to."""
    duplicated_values = attribute.values.exclude(pk=value.pk).filter(slug=value.slug)
    if duplicated_values.exists():
        raise ValidationError(
            {
                "name": ValidationError(
                    f"Value with slug {value.slug} already exists.",
                    code=ProductErrorCode.ALREADY_EXISTS.value,
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
        model = models.AttributeValue
        description = "Creates a value for an attribute."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        cleaned_input["slug"] = slugify(cleaned_input["name"])
        return cleaned_input

    @classmethod
    def clean_instance(cls, info, instance):
        validate_value_is_unique(instance.attribute, instance)
        super().clean_instance(info, instance)

    @classmethod
    def perform_mutation(cls, _root, info, attribute_id, input):
        attribute = cls.get_node_or_error(info, attribute_id, only_type=Attribute)
        instance = models.AttributeValue(attribute=attribute)
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
        model = models.AttributeValue
        description = "Updates value of an attribute."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        if "name" in cleaned_input:
            cleaned_input["slug"] = slugify(cleaned_input["name"])
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
        model = models.AttributeValue
        description = "Deletes a value of an attribute."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response


class ProductTypeReorderAttributes(BaseMutation):
    product_type = graphene.Field(
        ProductType, description="Product type from which attributes are reordered."
    )

    class Meta:
        description = "Reorder the attributes of a product type."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    class Arguments:
        product_type_id = graphene.Argument(
            graphene.ID, required=True, description="ID of a product type."
        )
        type = AttributeTypeEnum(
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

        if type == AttributeTypeEnum.PRODUCT:
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
        operations = {}

        # Resolve the attributes
        for move_info in moves:
            attribute_pk = from_global_id_strict_type(
                move_info.id, only_type=Attribute, field="moves"
            )

            try:
                m2m_info = attributes_m2m.get(attribute_id=int(attribute_pk))
            except ObjectDoesNotExist:
                raise ValidationError(
                    {
                        "moves": ValidationError(
                            f"Couldn't resolve to an attribute: {move_info.id}",
                            code=ProductErrorCode.NOT_FOUND,
                        )
                    }
                )
            operations[m2m_info.pk] = move_info.sort_order

        with transaction.atomic():
            perform_reordering(attributes_m2m, operations)
        return ProductTypeReorderAttributes(product_type=product_type)


class AttributeReorderValues(BaseMutation):
    attribute = graphene.Field(
        Attribute, description="Attribute from which values are reordered."
    )

    class Meta:
        description = "Reorder the values of an attribute."
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

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
            attribute = models.Attribute.objects.prefetch_related("values").get(pk=pk)
        except ObjectDoesNotExist:
            raise ValidationError(
                {
                    "attribute_id": ValidationError(
                        f"Couldn't resolve to an attribute: {attribute_id}",
                        code=ProductErrorCode.NOT_FOUND,
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
                            code=ProductErrorCode.NOT_FOUND,
                        )
                    }
                )
            operations[m2m_info.pk] = move_info.sort_order

        with transaction.atomic():
            perform_reordering(values_m2m, operations)
        attribute.refresh_from_db(fields=["values"])
        return AttributeReorderValues(attribute=attribute)
