import graphene
from graphene.types import InputObjectType

from ....graphql.product.types import Category
from ....graphql.utils import get_node
from ....product import models
from ...category.forms import CategoryForm
from ..core.mutations import (
    BaseMutation, ModelDeleteMutation, ModelFormMutation,
    ModelFormUpdateMutation, StaffMemberRequiredMutation, convert_form_errors)
from ..utils import get_attributes_dict_from_list


class CategoryCreateMutation(StaffMemberRequiredMutation, ModelFormMutation):
    class Arguments:
        parent_id = graphene.ID()

    class Meta:
        description = 'Creates a new category.'
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
        description = 'Updates an existing category.'
        form_class = CategoryForm

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        kwargs = super().get_form_kwargs(root, info, **input)
        kwargs['parent_pk'] = kwargs['instance'].parent_id
        return kwargs


class CategoryDelete(StaffMemberRequiredMutation, ModelDeleteMutation):
    class Meta:
        description = 'Deletes a category.'
        model = models.Category


class AttributeValueInput(InputObjectType):
    slug = graphene.String(required=True)
    value = graphene.String(required=True)


class BaseProductMutateMixin(BaseMutation):
    @classmethod
    def mutate(cls, root, info, *args, **kwargs):
        form_kwargs = cls.get_form_kwargs(root, info, **kwargs)
        attributes = form_kwargs.get('data').pop('attributes', None)
        form = cls._meta.form_class(**form_kwargs)
        if form.is_valid():
            if attributes:
                attr_slug_id = dict(
                    form.instance.product_type.product_attributes.values_list(
                        'slug', 'id'))
                form.instance.attributes = get_attributes_dict_from_list(
                    attributes=attributes, attr_slug_id=attr_slug_id)
            instance = form.save()
            kwargs = {cls._meta.return_field_name: instance}
            return cls(errors=[], **kwargs)
        errors = convert_form_errors(form)
        return cls(errors=errors)
