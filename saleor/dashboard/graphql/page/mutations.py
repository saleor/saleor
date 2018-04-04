from ....page import models
from ...page.forms import PageForm
from ..core.mutations import (
    ModelDeleteMutation, ModelFormMutation, ModelFormUpdateMutation,
    StaffMemberRequiredMutation)
from .decorators import must_be_unprotected


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

    @classmethod
    @must_be_unprotected
    def _delete_instance(cls, instance):
        return super(PageDelete, cls)._delete_instance(instance)
