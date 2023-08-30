from typing import Dict, List

import graphene
from django.core.exceptions import ValidationError

from ....attribute import AttributeInputType
from ....attribute import models as models
from ....attribute.error_codes import AttributeErrorCode
from ....core.utils import generate_unique_slug
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import AttributeError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Attribute, AttributeValue
from ..utils import check_permissions_for_attribute
from .attribute_create import AttributeValueCreateInput
from .mixins import AttributeMixin
from .validators import validate_value_is_unique


class AttributeValueCreate(AttributeMixin, ModelMutation):
    ATTRIBUTE_VALUES_FIELD = "input"

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
        auto_permission_message = False
        model = models.AttributeValue
        object_type = AttributeValue
        description = (
            "Creates a value for an attribute.\n\n"
            "Depending on the attribute type, "
            "it requires different permissions to create:\n"
            "-`PRODUCT_TYPE`: Requires one of the following permissions: "
            "`MANAGE_PRODUCTS` or `MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES`.\n"
            "-`PAGE_TYPE`: `MANAGE_PRODUCTS` or `MANAGE_PAGES` or "
            "`MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES`.\n"
            "\n\nDEPRECATED in Saleor 4.0, for attribute type:\n"
            " - `PAGE_TYPE`, `MANAGE_PAGES` permission will be required,\n"
            " - `PRODUCT_TYPE`, `MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES` permission will "
            "be required.\n"
        )
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        if "name" in cleaned_input:
            cleaned_input["slug"] = generate_unique_slug(
                instance,
                cleaned_input["name"],
                additional_search_lookup={"attribute_id": instance.attribute_id},
            )
        input_type = instance.attribute.input_type

        is_swatch_attr = input_type == AttributeInputType.SWATCH
        errors: Dict[str, List[ValidationError]] = {}
        if not is_swatch_attr:
            for field in cls.ONLY_SWATCH_FIELDS:
                if cleaned_input.get(field):
                    errors[field] = [
                        ValidationError(
                            f"The field {field} can be defined only for swatch attributes.",  # noqa: E501
                            code=AttributeErrorCode.INVALID.value,
                        )
                    ]
        else:
            try:
                cls.validate_swatch_attr_value(cleaned_input)
            except ValidationError as error:
                errors["value"] = error.error_dict[cls.ATTRIBUTE_VALUES_FIELD]
                errors["fileUrl"] = error.error_dict[cls.ATTRIBUTE_VALUES_FIELD]

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def clean_instance(cls, info: ResolveInfo, instance):
        validate_value_is_unique(instance.attribute, instance)
        super().clean_instance(info, instance)

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, attribute_id, input
    ):
        attribute = cls.get_node_or_error(info, attribute_id, only_type=Attribute)
        instance = models.AttributeValue(attribute=attribute)
        check_permissions_for_attribute(info.context, attribute, "create")
        cleaned_input = cls.clean_input(info, instance, input)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)

        instance.save()
        cls._save_m2m(info, instance, cleaned_input)
        cls.post_save_action(info, instance, cleaned_input)
        return AttributeValueCreate(attribute=attribute, attributeValue=instance)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.attribute_value_created, instance)
        cls.call_event(manager.attribute_updated, instance.attribute)
