import graphene

from ....page import models
from ...page.forms import PageForm
from ..mutations import (
    ModelDeleteMutation, ModelFormMutation, ModelFormUpdateMutation)


class PageCreate(ModelFormMutation):
    class Meta:
        form_class = PageForm


class PageUpdate(ModelFormUpdateMutation):
    class Meta:
        form_class = PageForm


class PageDelete(ModelDeleteMutation):

    class Meta:
        model = models.Page
