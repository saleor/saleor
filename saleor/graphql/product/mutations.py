import graphene

from ...dashboard.category.forms import CategoryForm
from ...product.models import Category
from .types import CategoryType


class Mutation(graphene.Mutation):
    errors = graphene.List(graphene.String)

    def mutate(self, info):
        raise NotImplementedError


class CategoryCreateInput(graphene.InputObjectType):
    name = graphene.String()
    description = graphene.String()
    parent = graphene.Int()


class CategoryCreate(Mutation):
    category = graphene.Field(CategoryType)

    class Arguments:
        input = CategoryCreateInput()

    def mutate(self, info, input):
        category = Category()
        form = CategoryForm(input, instance=category, parent_pk=input.parent)
        if form.is_valid():
            category = form.save()
            errors = []
        else:
            errors = form.errors
        return CategoryCreate(category=category, errors=errors)


class CategoryUpdate(Mutation):
    category = graphene.Field(CategoryType)

    class Arguments:
        input = CategoryCreateInput()
        pk = graphene.Int()

    def mutate(self, info, input, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            errors = ['not-found']
            category = None
        else:
            form = CategoryForm(input, instance=category, parent_pk=input.parent)
            if form.is_valid():
                category = form.save()
                errors = []
            else:
                errors = form.errors
        return CategoryUpdate(category=category, errors=errors)


class CategoryDelete(Mutation):
    class Arguments:
        pk = graphene.Int()

    def mutate(self, info, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            errors = ['not-found']
        else:
            category.delete()
            errors = []
        return CategoryDelete(errors=errors)
