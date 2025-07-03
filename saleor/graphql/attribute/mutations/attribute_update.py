import graphene
from django.core.exceptions import ValidationError

from ....attribute import models as models
from ....attribute.error_codes import AttributeErrorCode
from ....permission.enums import ProductTypePermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.descriptions import DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_ATTRIBUTES
from ...core.enums import MeasurementUnitsEnum
from ...core.mutations import ModelWithExtRefMutation
from ...core.types import AttributeError, BaseInputObjectType, NonNullList
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..descriptions import AttributeDescriptions, AttributeValueDescriptions
from ..types import Attribute
from .attribute_create import AttributeValueInput
from .mixins import AttributeMixin


class AttributeValueUpdateInput(AttributeValueInput):
    name = graphene.String(required=False, description=AttributeValueDescriptions.NAME)

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES


class AttributeUpdateInput(BaseInputObjectType):
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
        + DEPRECATED_IN_3X_INPUT
    )
    filterable_in_dashboard = graphene.Boolean(
        description=AttributeDescriptions.FILTERABLE_IN_DASHBOARD
    )
    storefront_search_position = graphene.Int(
        required=False,
        description=AttributeDescriptions.STOREFRONT_SEARCH_POSITION
        + DEPRECATED_IN_3X_INPUT,
    )
    available_in_grid = graphene.Boolean(
        required=False,
        description=AttributeDescriptions.AVAILABLE_IN_GRID + DEPRECATED_IN_3X_INPUT,
    )
    external_reference = graphene.String(
        description="External ID of this product.", required=False
    )

    class Meta:
        doc_category = DOC_CATEGORY_ATTRIBUTES
        description = (
            "Represents an input for update of attribute.\n\n"
            "NOTE: Deprecated fields `filterableInStorefront`, "
            "`storefrontSearchPosition` and `availableInGrid` are not supported in "
            "bulk mutations: `attributeBulkCreate`, `attributeBulkUpdate`."
        )


class AttributeUpdate(AttributeMixin, ModelWithExtRefMutation):
    # Needed by AttributeMixin,
    # represents the input name for the passed list of values
    ATTRIBUTE_VALUES_FIELD = "add_values"

    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(required=False, description="ID of an attribute to update.")
        external_reference = graphene.String(
            required=False,
            description="External ID of an attribute to update.",
        )
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
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.ATTRIBUTE_UPDATED,
                description="An attribute was updated.",
            ),
        ]

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
                            msg, code=AttributeErrorCode.INVALID.value
                        )
                    }
                )
        return remove_values

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        for attribute_value in cleaned_data.get("remove_values", []):
            attribute_value.delete()

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, external_reference=None, id=None, input
    ):
        instance = cls.get_instance(info, external_reference=external_reference, id=id)

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
        return AttributeUpdate(attribute=ChannelContext(instance, None))

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.attribute_updated, instance)
