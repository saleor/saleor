from typing import Tuple, Union

import graphene
from django.core.exceptions import ValidationError

from ....attribute import AttributeInputType
from ....attribute import models as models
from ....attribute.error_codes import AttributeErrorCode
from ....core.exceptions import PermissionDenied
from ....permission.enums import PageTypePermissions, ProductTypePermissions
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_310, DEPRECATED_IN_3X_INPUT
from ...core.enums import MeasurementUnitsEnum
from ...core.fields import JSONString
from ...core.mutations import ModelMutation
from ...core.types import AttributeError, NonNullList
from ...plugins.dataloaders import get_plugin_manager_promise
from ..descriptions import AttributeDescriptions, AttributeValueDescriptions
from ..enums import AttributeEntityTypeEnum, AttributeInputTypeEnum, AttributeTypeEnum
from ..types import Attribute
from .mixins import AttributeMixin


class AttributeValueInput(graphene.InputObjectType):
    value = graphene.String(description=AttributeValueDescriptions.VALUE)
    rich_text = JSONString(
        description=AttributeValueDescriptions.RICH_TEXT
        + DEPRECATED_IN_3X_INPUT
        + "The rich text attribute hasn't got predefined value, so can be specified "
        "only from instance that supports the given attribute."
    )
    plain_text = graphene.String(
        description=AttributeValueDescriptions.PLAIN_TEXT
        + DEPRECATED_IN_3X_INPUT
        + "The plain text attribute hasn't got predefined value, so can be specified "
        "only from instance that supports the given attribute."
    )
    file_url = graphene.String(
        required=False,
        description="URL of the file attribute. Every time, a new value is created.",
    )
    content_type = graphene.String(required=False, description="File content type.")
    external_reference = graphene.String(
        description="External ID of this attribute value." + ADDED_IN_310,
        required=False,
    )


class AttributeValueCreateInput(AttributeValueInput):
    name = graphene.String(required=True, description=AttributeValueDescriptions.NAME)


class AttributeCreateInput(graphene.InputObjectType):
    input_type = AttributeInputTypeEnum(description=AttributeDescriptions.INPUT_TYPE)
    entity_type = AttributeEntityTypeEnum(description=AttributeDescriptions.ENTITY_TYPE)
    name = graphene.String(required=True, description=AttributeDescriptions.NAME)
    slug = graphene.String(required=False, description=AttributeDescriptions.SLUG)
    type = AttributeTypeEnum(description=AttributeDescriptions.TYPE, required=True)
    unit = MeasurementUnitsEnum(description=AttributeDescriptions.UNIT, required=False)
    values = NonNullList(
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
    external_reference = graphene.String(
        description="External ID of this attribute." + ADDED_IN_310, required=False
    )


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
        object_type = Attribute
        description = "Creates an attribute."
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        if cleaned_input.get(
            "input_type"
        ) == AttributeInputType.REFERENCE and not cleaned_input.get("entity_type"):
            raise ValidationError(
                {
                    "entity_type": ValidationError(
                        "Entity type is required when REFERENCE input type is used.",
                        code=AttributeErrorCode.REQUIRED.value,
                    )
                }
            )
        return cleaned_input

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input
    ):
        # check permissions based on attribute type
        permissions: Union[Tuple[ProductTypePermissions], Tuple[PageTypePermissions]]
        if input["type"] == AttributeTypeEnum.PRODUCT_TYPE.value:
            permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        else:
            permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        if not cls.check_permissions(info.context, permissions):
            raise PermissionDenied(permissions=permissions)

        instance = models.Attribute()

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
        cls.post_save_action(info, instance, cleaned_input)
        # Return the attribute that was created
        return AttributeCreate(attribute=instance)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.attribute_created, instance)
