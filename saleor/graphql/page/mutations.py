from ...dashboard.page.forms import PageForm
from ...page import models
from ..core.mutations import (
    ModelDeleteMutation, ModelFormMutation, ModelFormUpdateMutation,
    StaffMemberRequiredMixin)
# TODO: This dummy import allows application to start. Find out why
from .types import Page


class PageCreate(StaffMemberRequiredMixin, ModelFormMutation):
    permissions = 'page.edit_page'
    class Meta:
        description = 'Creates a new page.'
        form_class = PageForm


class PageUpdate(StaffMemberRequiredMixin, ModelFormUpdateMutation):
    permissions = 'page.edit_page'
    class Meta:
        description = 'Updates an existing page.'
        form_class = PageForm


class PageDelete(StaffMemberRequiredMixin, ModelDeleteMutation):
    permissions = 'page.edit_page'
    class Meta:
        description = 'Deletes a page.'
        model = models.Page
