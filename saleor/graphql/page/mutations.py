from ...dashboard.page.forms import PageForm
from ...page import models
from ..core.mutations import (
    ModelDeleteMutation, ModelFormMutation, ModelFormUpdateMutation,
    StaffMemberRequiredMixin)
from .decorators import must_be_unprotected


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

    @classmethod
    @must_be_unprotected
    def _delete_instance(cls, instance):
        return super(PageDelete, cls)._delete_instance(instance)
