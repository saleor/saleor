import graphene

from ....page import models
from ...page.forms import PageForm
from ..core.mutations import (
    ModelDeleteMutation, ModelFormMutation, ModelFormUpdateMutation,
    StaffMemberRequiredMutation)


class PageCreate(StaffMemberRequiredMutation, ModelFormMutation):
    class Meta:
        description = "Creates a new page."
        form_class = PageForm


class PageUpdate(StaffMemberRequiredMutation, ModelFormUpdateMutation):
    class Meta:
        description = "Updates a existing page."
        form_class = PageForm


class PageDelete(StaffMemberRequiredMutation, ModelDeleteMutation):
    class Meta:
        description = "Permanently deletes a page."
        model = models.Page
