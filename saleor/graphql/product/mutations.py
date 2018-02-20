import graphene

from ...dashboard.category.forms import CategoryForm
from ..core.mutations import BaseMutation, ModelFormMutation, ModelFormUpdateMutation
from ..utils import get_node
from .types import Category


class CategoryCreateMutation(ModelFormMutation):
    class Arguments:
        parent_id = graphene.ID()

    class Meta:
        form_class = CategoryForm

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        parent_id = input.pop('parent_id', None)
        kwargs = super().get_form_kwargs(root, info, **input)
        if parent_id:
            parent = get_node(info, parent_id, only_type=Category)
        else:
            parent = None
        kwargs['parent_pk'] = parent.pk if parent else None
        return kwargs


class CategoryUpdateMutation(ModelFormUpdateMutation):
    class Meta:
        form_class = CategoryForm

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        kwargs = super().get_form_kwargs(root, info, **input)
        kwargs['parent_pk'] = kwargs['instance'].parent_id
        return kwargs


class CategoryDelete(BaseMutation):
    category = graphene.Field(Category)

    class Arguments:
        id = graphene.ID()

    def mutate(self, info, id):
        category = get_node(info, id, only_type=Category)
        category.delete()
        return CategoryDelete(category=category)
