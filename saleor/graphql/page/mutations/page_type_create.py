from collections import defaultdict
from typing import TYPE_CHECKING

import graphene
from django.core.exceptions import ValidationError

from ....attribute import AttributeType
from ....page import models
from ....page.error_codes import PageErrorCode
from ....permission.enums import PageTypePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PAGES
from ...core.mutations import ModelMutation
from ...core.types import BaseInputObjectType, NonNullList, PageError
from ...core.validators import validate_slug_and_generate_if_needed
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import PageType

if TYPE_CHECKING:
    from ....attribute.models import Attribute


class PageTypeCreateInput(BaseInputObjectType):
    name = graphene.String(description="Name of the page type.")
    slug = graphene.String(description="Page type slug.")
    add_attributes = NonNullList(
        graphene.ID,
        description="List of attribute IDs to be assigned to the page type.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAGES


class PageTypeMixin:
    @classmethod
    def validate_attributes(
        cls,
        errors: dict[str, list[ValidationError]],
        attributes: list["Attribute"],
        field: str,
    ):
        """All attributes must be page type attribute.

        Raise an error if any of the attributes are not page attribute.
        """
        if attributes:
            not_valid_attributes = [
                graphene.Node.to_global_id("Attribute", attr.pk)
                for attr in attributes
                if attr.type != AttributeType.PAGE_TYPE
            ]
            if not_valid_attributes:
                error = ValidationError(
                    "Only page type attributes allowed.",
                    code=PageErrorCode.INVALID.value,
                    params={"attributes": not_valid_attributes},
                )
                errors[field].append(error)


class PageTypeCreate(PageTypeMixin, ModelMutation):
    class Arguments:
        input = PageTypeCreateInput(
            description="Fields required to create page type.", required=True
        )

    class Meta:
        description = "Create a new page type."
        model = models.PageType
        object_type = PageType
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        errors = defaultdict(list)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = PageErrorCode.REQUIRED.value
            errors["slug"].append(error)

        cls.validate_attributes(
            errors, cleaned_input.get("add_attributes"), "add_attributes"
        )

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        attributes = cleaned_data.get("add_attributes")
        if attributes is not None:
            instance.page_attributes.add(*attributes)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.page_type_created, instance)
