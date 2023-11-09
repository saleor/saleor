import graphene

from ....page import models
from ....permission.enums import PagePermissions
from ...attribute.utils import PageAttributeAssignmentMixin
from ...core import ResolveInfo
from ...core.types import PageError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Page
from .page_create import PageCreate, PageInput


class PageUpdate(PageCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a page to update.")
        input = PageInput(
            required=True, description="Fields required to update a page."
        )

    class Meta:
        description = "Updates an existing page."
        model = models.Page
        object_type = Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def clean_attributes(cls, attributes: dict, page_type: models.PageType):
        attributes_qs = page_type.page_attributes.prefetch_related("values")
        cleaned_attributes = PageAttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, creation=False, is_page_attributes=True
        )
        return cleaned_attributes

    @classmethod
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        super(PageCreate, cls).save(info, instance, cleaned_input)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.page_updated, instance)
