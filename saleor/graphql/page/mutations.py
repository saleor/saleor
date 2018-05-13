from graphql_jwt.exceptions import PermissionDenied

from ...dashboard.page.forms import PageForm
from ...page import models
from ..core.mutations import (
    ModelDeleteMutation, ModelFormMutation, ModelFormUpdateMutation,
    StaffMemberRequiredMixin)


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
    def delete_instance(cls, instance):
        """This override checks if the passed instance is not protected.

        If the instance is existing and is protected,
        it raises a `PermissionDenied`.

        If the instance is None (non existing) or non-protected,
        it will call the wrapped Mutator function,
        and pass the instance as a keyword parameter.
        """
        if instance and instance.is_protected:
            raise PermissionDenied()
        return super(PageDelete, cls).delete_instance(instance)
