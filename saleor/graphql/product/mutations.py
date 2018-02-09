import graphene

from ...dashboard.category.forms import CategoryForm
from ...product.models import Category
from ..core.types import ErrorType
from ..utils import get_object_or_none
from .types import CategoryType


def convert_form_errors(form):
    """Convert ModelForm errors into a list of ErrorType objects"""
    errors = []
    for field in form.errors:
        for message in form.errors[field]:
            errors.append(ErrorType(field=field, message=message))
    return errors


class CategoryMutation(graphene.Mutation):
    category = graphene.Field(CategoryType)
    errors = graphene.List(ErrorType)

    def mutate(self, info):
        raise NotImplementedError


class CategoryInput(graphene.InputObjectType):
    name = graphene.String()
    description = graphene.String()
    parent = graphene.Int()


class CategoryCreate(CategoryMutation):
    class Arguments:
        data = CategoryInput()

    def mutate(self, info, data):
        category = Category()
        errors = []
        form = CategoryForm(data, instance=category, parent_pk=data.parent)
        if form.is_valid():
            category = form.save()
        else:
            errors = convert_form_errors(form)
        return CategoryCreate(category=category, errors=errors)


class CategoryUpdate(CategoryMutation):
    class Arguments:
        data = CategoryInput()
        pk = graphene.Int()

    def mutate(self, info, data, pk):
        category = get_object_or_none(Category, pk=pk)
        errors = []
        if category:
            form = CategoryForm(
                data, instance=category, parent_pk=category.parent_id)
            if form.is_valid():
                category = form.save()
            else:
                errors = convert_form_errors(form)
        return CategoryCreate(category=category, errors=errors)


class CategoryDelete(CategoryMutation):
    class Arguments:
        pk = graphene.Int()

    def mutate(self, info, pk):
        category = get_object_or_none(Category, pk=pk)
        if category:
            category.delete()
        return CategoryCreate(category=category)
