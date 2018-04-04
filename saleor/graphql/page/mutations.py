from ...dashboard.page.forms import PageForm
from ...page import models
from ..core.mutations import (
    ModelDeleteMutation, ModelFormMutation, ModelFormUpdateMutation,
    StaffMemberRequiredMutation)
# TODO: This dummy import allows application to start. Find out why
from .types import Page


class PageCreate(StaffMemberRequiredMutation, ModelFormMutation):
    class Meta:
        description = 'Creates a new page.'
        form_class = PageForm


class PageUpdate(StaffMemberRequiredMutation, ModelFormUpdateMutation):
    class Meta:
        description = 'Updates an existing page.'
        form_class = PageForm


class PageDelete(StaffMemberRequiredMutation, ModelDeleteMutation):
    class Meta:
        description = 'Deletes a page.'
        model = models.Page
