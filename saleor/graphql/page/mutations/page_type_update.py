from collections import defaultdict

import graphene
from django.core.exceptions import ValidationError

from ....page import models
from ....page.error_codes import PageErrorCode
from ....permission.enums import PageTypePermissions
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PAGES
from ...core.mutations import ModelMutation
from ...core.types import NonNullList, PageError
from ...core.validators import validate_slug_and_generate_if_needed
from ...plugins.dataloaders import get_plugin_manager_promise
from ...utils.validators import check_for_duplicates
from ..types import PageType
from .page_type_create import PageTypeCreateInput, PageTypeMixin


class PageTypeUpdateInput(PageTypeCreateInput):
    remove_attributes = NonNullList(
        graphene.ID,
        description="List of attribute IDs to be assigned to the page type.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_PAGES


class PageTypeUpdate(PageTypeMixin, ModelMutation):
    class Arguments:
        id = graphene.ID(description="ID of the page type to update.")
        input = PageTypeUpdateInput(
            description="Fields required to update page type.", required=True
        )

    class Meta:
        description = "Update page type."
        model = models.PageType
        object_type = PageType
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        errors = defaultdict(list)
        error = check_for_duplicates(
            data, "add_attributes", "remove_attributes", "attributes"
        )
        if error:
            error.code = PageErrorCode.DUPLICATED_INPUT_ITEM.value
            errors["attributes"].append(error)

        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = PageErrorCode.REQUIRED
            errors["slug"].append(error)

        add_attributes = cleaned_input.get("add_attributes")
        cls.validate_attributes(errors, add_attributes, "add_attributes")

        remove_attributes = cleaned_input.get("remove_attributes")
        cls.validate_attributes(errors, remove_attributes, "remove_attributes")

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, instance, cleaned_data):
        super()._save_m2m(info, instance, cleaned_data)
        remove_attributes = cleaned_data.get("remove_attributes")
        add_attributes = cleaned_data.get("add_attributes")
        if remove_attributes is not None:
            instance.page_attributes.remove(*remove_attributes)
        if add_attributes is not None:
            instance.page_attributes.add(*add_attributes)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.page_type_updated, instance)
