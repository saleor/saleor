from typing import List

import graphene
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.template.defaultfilters import slugify

from ....product import models
from ...core.mutations import (
    BaseMutation,
    ClearMetaBaseMutation,
    ModelDeleteMutation,
    ModelMutation,
    UpdateMetaBaseMutation,
)
from ...core.utils import from_global_id_strict_type
from ...product.enums import AttributeTypeEnum
from ...product.types import ProductType
from ..descriptions import AttributeDescriptions, AttributeValueDescriptions
from ..types import Attribute


class AttributeValueCreateInput(graphene.InputObjectType):
    name = graphene.String(required=True, description=AttributeValueDescriptions.NAME)
    value = graphene.String(description=AttributeValueDescriptions.VALUE)


class AttributeCreateInput(graphene.InputObjectType):
    name = graphene.String(required=True, description=AttributeDescriptions.NAME)
    slug = graphene.String(required=False, description=AttributeDescriptions.SLUG)
    values = graphene.List(
        AttributeValueCreateInput, description=AttributeDescriptions.VALUES
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


class AttributeAssignInput(graphene.InputObjectType):
    attribute_id = graphene.ID(
        required=True, description="The ID of the attribute to assign"
    )
    attribute_type = AttributeTypeEnum(
        required=True, description="The attribute type to be assigned as."
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
                raise ValidationError({cls.ATTRIBUTE_VALUES_FIELD: msg})

        new_slugs = [slugify(value_data["name"]) for value_data in values_input]
        if len(set(new_slugs)) != len(new_slugs):
            raise ValidationError(
                {cls.ATTRIBUTE_VALUES_FIELD: "Provided values are not unique."}
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
                for field in validation_errors.message_dict:
                    if field == "attribute":
                        continue
                    for msg in validation_errors.message_dict[field]:
                        raise ValidationError({cls.ATTRIBUTE_VALUES_FIELD: msg})
        cls.check_values_are_unique(values_input, attribute)

    @classmethod
    def clean_attribute(cls, instance, cleaned_input):
        input_slug = cleaned_input.get("slug", None)
        if input_slug is None:
            cleaned_input["slug"] = slugify(cleaned_input["name"])
        elif input_slug == "":
            raise ValidationError({"slug": "The attribute's slug cannot be blank."})

        query = models.Attribute.objects.filter(slug=cleaned_input["slug"])

        if instance.pk:
            query = query.exclude(pk=instance.pk)

        if query.exists():
            raise ValidationError({"slug": "This attribute's slug already exists."})

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
        permissions = ("product.manage_products",)

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        instance = models.Attribute()

        # Do cleaning and uniqueness checks
        cleaned_input = cls.clean_input(info, instance, data.get("input"))
        cls.clean_attribute(instance, cleaned_input)
        cls.clean_values(cleaned_input, instance)

        # Construct the attribute
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance)

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
        permissions = ("product.manage_products",)

    @classmethod
    def clean_remove_values(cls, cleaned_input, instance):
        """Check if the values to be removed are assigned to the given attribute."""
        remove_values = cleaned_input.get("remove_values", [])
        for value in remove_values:
            if value.attribute != instance:
                msg = "Value %s does not belong to this attribute." % value
                raise ValidationError({"remove_values": msg})
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
        cls.clean_instance(instance)

        # Commit it
        instance.save()
        cls._save_m2m(info, instance, cleaned_input)

        # Return the attribute that was created
        return AttributeUpdate(attribute=instance)


class BaseAttributeAssignmentMutation(BaseMutation):
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
        abstract = True

    @classmethod
    def check_permissions(cls, user):
        return user.has_perm("product.manage_products")

    @classmethod
    def get_operations(cls, info, operations: List[AttributeAssignInput]):
        """Resolves all passed global ids into integer PKs of the Attribute type."""
        product_attrs_pks = []
        variant_attrs_pks = []

        for operation in operations:
            pk = from_global_id_strict_type(
                info, operation.attribute_id, only_type=Attribute, field="operations"
            )
            if operation.attribute_type == AttributeTypeEnum.PRODUCT:
                product_attrs_pks.append(pk)
            else:
                variant_attrs_pks.append(pk)

        return product_attrs_pks, variant_attrs_pks


class AttributeAssign(BaseAttributeAssignmentMutation):
    class Meta:
        description = "Assign attributes to a given product type."

    @classmethod
    def clean_operations(cls, product_type, product_attrs_pks, variant_attrs_pks):
        """Ensures the requested attributes are not already assigned
        to that product type."""
        qs = (
            models.Attribute.get_assigned_attributes(product_type.pk)
            .values_list("name", "slug")
            .filter(Q(pk__in=product_attrs_pks) | Q(pk__in=variant_attrs_pks))
        )

        invalid_attributes = list(qs)
        if invalid_attributes:
            msg = ", ".join([f"{name} ({slug})" for name, slug in invalid_attributes])
            raise ValidationError(
                {
                    "operations": (
                        f"{msg} have already been assigned to this product type."
                    )
                }
            )

    @classmethod
    def save_field_values(cls, product_type, field, pks):
        """Add in bulk the PKs to assign to a given product type."""
        getattr(product_type, field).add(*pks)

    @classmethod
    def perform_mutation(
        cls, _root, info, product_type_id: str, operations: List[AttributeAssignInput]
    ):
        # Retrieve the requested product type
        product_type = graphene.Node.get_node_from_global_id(
            info, product_type_id, only_type=ProductType
        )  # type: models.ProductType

        # Resolve all the passed IDs to ints
        product_attrs_pks, variant_attrs_pks = cls.get_operations(info, operations)

        if variant_attrs_pks and not product_type.has_variants:
            raise ValidationError(
                {"operations": "Variants are disabled in this product type."}
            )

        # Ensure the attribute are assignable
        cls.clean_operations(product_type, product_attrs_pks, variant_attrs_pks)

        # Commit
        cls.save_field_values(product_type, "product_attributes", product_attrs_pks)
        cls.save_field_values(product_type, "variant_attributes", variant_attrs_pks)

        return cls(product_type=product_type)


class AttributeUnAssign(BaseAttributeAssignmentMutation):
    class Meta:
        description = "Un-assign attributes from a given product type."

    @classmethod
    def save_field_values(cls, product_type, field, pks):
        """Add in bulk the PKs to assign to a given product type."""
        getattr(product_type, field).remove(*pks)

    @classmethod
    def perform_mutation(
        cls, _root, info, product_type_id: str, operations: List[AttributeAssignInput]
    ):
        # Retrieve the requested product type
        product_type = graphene.Node.get_node_from_global_id(
            info, product_type_id, only_type=ProductType
        )  # type: models.ProductType

        # Resolve all the passed IDs to ints
        product_attrs_pks, variant_attrs_pks = cls.get_operations(info, operations)

        # Commit
        cls.save_field_values(product_type, "product_attributes", product_attrs_pks)
        cls.save_field_values(product_type, "variant_attributes", variant_attrs_pks)

        return cls(product_type=product_type)


class AttributeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of an attribute to delete.")

    class Meta:
        model = models.Attribute
        description = "Deletes an attribute."
        permissions = ("product.manage_products",)


class AttributeUpdateMeta(UpdateMetaBaseMutation):
    class Meta:
        model = models.Attribute
        description = "Update public metadata for Attribute "
        permissions = ("product.manage_products",)
        public = True


class AttributeClearMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears public metadata item for Attribute"
        model = models.Attribute
        permissions = ("product.manage_products",)
        public = True


class AttributeUpdatePrivateMeta(UpdateMetaBaseMutation):
    class Meta:
        description = "Update public metadata for Attribute"
        model = models.Attribute
        permissions = ("product.manage_products",)
        public = False


class AttributeClearPrivateMeta(ClearMetaBaseMutation):
    class Meta:
        description = "Clears public metadata item for Attribute"
        model = models.Attribute
        permissions = ("product.manage_products",)
        public = False


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
        permissions = ("product.manage_products",)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        cleaned_input["slug"] = slugify(cleaned_input["name"])
        return cleaned_input

    @classmethod
    def perform_mutation(cls, _root, info, attribute_id, input):
        attribute = cls.get_node_or_error(info, attribute_id, only_type=Attribute)

        instance = models.AttributeValue(attribute=attribute)
        cleaned_input = cls.clean_input(info, instance, input)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(instance)

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
        permissions = ("product.manage_products",)

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        if "name" in cleaned_input:
            cleaned_input["slug"] = slugify(cleaned_input["name"])
        return cleaned_input

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
        permissions = ("product.manage_products",)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response
