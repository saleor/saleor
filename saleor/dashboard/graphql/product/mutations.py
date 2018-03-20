import graphene

from ....graphql.product.types import Category, ProductType
from ....graphql.utils import get_node
from ....product import models
from ...category.forms import CategoryForm
# from ...product.forms import ProductForm
from .forms import ProductForm
from ..mutations import (
    BaseMutation, ModelDeleteMutation, ModelFormMutation,
    ModelFormUpdateMutation, StaffMemberRequiredMutation)


class CategoryCreateMutation(StaffMemberRequiredMutation, ModelFormMutation):
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


class CategoryUpdateMutation(
        StaffMemberRequiredMutation, ModelFormUpdateMutation):
    class Meta:
        form_class = CategoryForm

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        kwargs = super().get_form_kwargs(root, info, **input)
        kwargs['parent_pk'] = kwargs['instance'].parent_id
        return kwargs


class CategoryDelete(StaffMemberRequiredMutation, ModelDeleteMutation):
    class Meta:
        model = models.Category


class ProductCreateMutation(ModelFormMutation):
    class Arguments:
        product_type = graphene.ID
        category = graphene.ID

    class Meta:
        form_class = ProductForm

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        product_type_id = input.pop('product_type', None)
        category_id = input.pop('category', None)
        product_type = get_node(info, product_type_id, only_type=ProductType)
        category = get_node(info, category_id, only_type=Category)
        kwargs = super().get_form_kwargs(root, info, **input)
        kwargs['data']['product_type'] = product_type.id
        kwargs['data']['category'] = category.id
        return kwargs
