import graphene
from graphene.types import InputObjectType

from ....graphql.product.types import Category, ProductType
from ....graphql.utils import get_node
from ....product import models
from ...category.forms import CategoryForm
from ..mutations import (
    ModelDeleteMutation, ModelFormMutation, ModelFormUpdateMutation,
    StaffMemberRequiredMutation)
from .forms import ProductForm


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


class ValuesInput(InputObjectType):
    name = graphene.String(required=True)
    value = graphene.String(required=True)


class ProductCreateMutation(ModelFormMutation):
    class Arguments:
        product_type_id = graphene.ID()
        category_id = graphene.ID()
        attributes = graphene.Argument(graphene.List(ValuesInput))

    class Meta:
        form_class = ProductForm
        # Exclude from input form fields
        # that are being overwritten by arguments
        exclude = ['product_type', 'category', 'attributes']

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        product_type_id = input.pop('product_type_id', None)
        category_id = input.pop('category_id', None)
        product_type = get_node(info, product_type_id, only_type=ProductType)
        category = get_node(info, category_id, only_type=Category)
        kwargs = super().get_form_kwargs(root, info, **input)
        kwargs['data']['product_type'] = product_type.id
        kwargs['data']['category'] = category.id
        return kwargs


class ProductDeleteMutation(ModelDeleteMutation):

    class Meta:
        model = models.Product


class ProductUpdateMutation(ModelFormUpdateMutation):
    class Arguments:
        attributes = graphene.Argument(graphene.List(ValuesInput))
        category_id = graphene.ID()

    class Meta:
        form_class = ProductForm
        # Exclude from input form fields
        # that are being overwritten by arguments
        exclude = ['product_type', 'category', 'attributes']

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        kwargs = super().get_form_kwargs(root, info, **input)
        instance = kwargs.get('instance')
        kwargs['data']['product_type'] = instance.product_type.id
        # Use provided category or existing one
        category_id = input.pop('category_id', None)
        if category_id:
            category = get_node(info, category_id, only_type=Category)
            kwargs['data']['category'] = category.id
        else:
            kwargs['data']['category'] = instance.category.id
        return kwargs
