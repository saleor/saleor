import graphene
from django.core.exceptions import ValidationError

from ....attribute import models as models
from ....attribute.error_codes import AttributeErrorCode
from ....core.permissions import ProductTypePermissions
from ...core.enums import MeasurementUnitsEnum
from ...core.mutations import ModelMutation
from ...core.types import AttributeError, NonNullList
from ...plugins.dataloaders import load_plugin_manager
from ..descriptions import AttributeDescriptions, AttributeValueDescriptions
from ..types import Attribute
from .attribute_create import AttributeValueInput
from .mixins import AttributeMixin


class AttributeValueUpdateInput(AttributeValueInput):
    name = graphene.String(required=False, description=AttributeValueDescriptions.NAME)


class AttributeUpdateInput(graphene.InputObjectType):
    name = graphene.String(description=AttributeDescriptions.NAME)
    slug = graphene.String(description=AttributeDescriptions.SLUG)
    unit = MeasurementUnitsEnum(description=AttributeDescriptions.UNIT, required=False)
    remove_values = NonNullList(
        graphene.ID,
        name="removeValues",
        description="IDs of values to be removed from this attribute.",
    )
    add_values = NonNullList(
        AttributeValueUpdateInput,
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
        object_type = Attribute
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
                msg = f"Value {value} does not belong to this attribute."
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
        cls.post_save_action(info, instance, cleaned_input)

        # Return the attribute that was created
        return AttributeUpdate(attribute=instance)

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        manager = load_plugin_manager(info.context)
        cls.call_event(manager.attribute_updated, instance)
