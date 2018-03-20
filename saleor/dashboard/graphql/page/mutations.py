import graphene

from ....page import models
from ...page.forms import PageForm
from ..mutations import (
    ModelDeleteMutation, ModelFormMutation, ModelFormUpdateMutation,
    StaffMemberRequiredMutation)


class PageCreate(StaffMemberRequiredMutation, ModelFormMutation):
    class Meta:
        form_class = PageForm


class PageUpdate(StaffMemberRequiredMutation, ModelFormUpdateMutation):
    class Meta:
        form_class = PageForm


class PageDelete(StaffMemberRequiredMutation, ModelDeleteMutation):
    class Meta:
        model = models.Page
