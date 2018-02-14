import graphene

from ...dashboard.category.forms import CategoryForm
from ...product.models import Category
from ..core.mutations import BaseMutation, ModelFormMutation
from ..utils import get_object_or_none
from .types import CategoryType


class CategoryMutation(ModelFormMutation):
    class Arguments:
        parent_pk = graphene.Int()

    class Meta:
        form_class = CategoryForm

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        parent_pk = input.pop('parent_pk', None)
        kwargs = super().get_form_kwargs(root, info, **input)
        kwargs['parent_pk'] = parent_pk
        return kwargs


class CategoryDelete(BaseMutation):
    category = graphene.Field(CategoryType)

    class Arguments:
        pk = graphene.Int()

    def mutate(self, info, pk):
        category = get_object_or_none(Category, pk=pk)
        if category:
            category.delete()
        return CategoryDelete(category=category)
