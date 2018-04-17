import graphene
from graphene.types import InputObjectType

from ...dashboard.category.forms import CategoryForm
from ...dashboard.product.forms import ProductTypeForm
from ...product import models
from ..core.mutations import (
    ModelDeleteMutation, ModelFormMutation,
    ModelFormUpdateMutation, StaffMemberRequiredMixin)
from ..utils import get_attributes_dict_from_list, get_node
from .forms import ProductForm, ProductVariantForm
from .types import Category, Product, ProductAttribute, ProductType


class CategoryCreateMutation(StaffMemberRequiredMixin, ModelFormMutation):
    permissions = 'category.edit_category'

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
        StaffMemberRequiredMixin, ModelFormUpdateMutation):
    permissions = 'category.edit_category'

    class Meta:
        description = 'Updates an existing category.'
        form_class = CategoryForm

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        kwargs = super().get_form_kwargs(root, info, **input)
        kwargs['parent_pk'] = kwargs['instance'].parent_id
        return kwargs


class CategoryDelete(StaffMemberRequiredMixin, ModelDeleteMutation):
    permissions = 'category.edit_category'

    class Meta:
        description = 'Deletes a category.'
        model = models.Category


class AttributeValueInput(InputObjectType):
    slug = graphene.String(required=True)
    value = graphene.String(required=True)


class ProductSave(ModelFormMutation):
    permissions = 'product.edit_product'

    class Meta:
        form_class = ProductForm

    @classmethod
    def save(cls, root, info, **kwargs):
        attributes = kwargs.pop('attributes', None)
        instance = super().save(root, info, **kwargs)
        if attributes and instance:
            attr_slug_id = dict(
                instance.product_type.product_attributes.values_list(
                    'slug', 'id'))
            instance.attributes = get_attributes_dict_from_list(
                attributes=attributes, attr_slug_id=attr_slug_id)
            instance.save()
        return instance


class ProductCreateMutation(
        StaffMemberRequiredMixin, ProductSave):
    permissions = 'product.edit_product'

    class Arguments:
        product_type_id = graphene.ID()
        category_id = graphene.ID()
        attributes = graphene.Argument(graphene.List(AttributeValueInput))

    class Meta:
        description = 'Creates a new product.'
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


class ProductUpdateMutation(
        StaffMemberRequiredMixin, ProductSave, ModelFormUpdateMutation):
    permissions = 'product.edit_product'

    class Arguments:
        attributes = graphene.Argument(graphene.List(AttributeValueInput))
        category_id = graphene.ID()

    class Meta:
        description = 'Update an existing product.'
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


class ProductDeleteMutation(StaffMemberRequiredMixin, ModelDeleteMutation):
    permissions = 'product.edit_product'

    class Meta:
        description = 'Deletes a product.'
        model = models.Product


class VariantSave(ModelFormMutation):
    permissions = 'product.edit_product'

    class Meta:
        form_class = ProductVariantForm

    @classmethod
    def save(cls, root, info, **kwargs):
        attributes = kwargs.pop('attributes', None)
        instance = super().save(root, info, **kwargs)
        if attributes and instance:
            attr_slug_id = dict(
                instance.product.product_type.variant_attributes.values_list(
                    'slug', 'id'))
            instance.attributes = get_attributes_dict_from_list(
                attributes=attributes, attr_slug_id=attr_slug_id)
            instance.save()
        return instance


class ProductVariantCreateMutation(
        StaffMemberRequiredMixin, VariantSave, ModelFormMutation):
    permissions = 'product.edit_product'

    class Arguments:
        attributes = graphene.Argument(graphene.List(AttributeValueInput))
        product_id= graphene.ID()

    class Meta:
        description = 'Creates a new variant for product'
        form_class = ProductVariantForm
        exclude = ['attributes']

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        product_id = input.pop('product_id', None)
        product = get_node(info, product_id, only_type=Product)
        variant = models.ProductVariant(product=product)
        kwargs = super().get_form_kwargs(root, info, **input)
        kwargs['instance'] = variant
        return kwargs


class ProductVariantUpdateMutation(
        StaffMemberRequiredMixin, VariantSave, ModelFormUpdateMutation):
    permissions = 'product.edit_product'

    class Arguments:
        attributes = graphene.Argument(graphene.List(AttributeValueInput))
        # product_id= graphene.ID()

    class Meta:
        description = 'Updates an existing variant for product'
        form_class = ProductVariantForm
        exclude = ['attributes']


class ProductVariantDeleteMutation(
        StaffMemberRequiredMixin, ModelDeleteMutation):
    permissions = 'product.edit_product'

    class Meta:
        description = 'Deletes a product variant.'
        model = models.ProductVariant


class ProductTypeCreateMutation(StaffMemberRequiredMixin, ModelFormMutation):
    permissions = 'product.edit_properties'

    class Meta:
        description = 'Creates a new product type.'
        form_class = ProductTypeForm

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        product_attributes = input.pop('product_attributes', None)
        if product_attributes:
            product_attributes = {
                get_node(info, pr_att_id, only_type=ProductAttribute)
                for pr_att_id in product_attributes}

        variant_attributes = input.pop('variant_attributes', None)
        if variant_attributes:
            variant_attributes = {
                get_node(info, pr_att_id, only_type=ProductAttribute)
                for pr_att_id in variant_attributes}

        kwargs = super().get_form_kwargs(root, info, **input)
        kwargs['data']['product_attributes'] = product_attributes
        kwargs['data']['variant_attributes'] = variant_attributes
        return kwargs


class ProductTypeUpdateMutation(
        StaffMemberRequiredMixin, ModelFormUpdateMutation):
    permissions = 'product.edit_properties'

    class Meta:
        description = 'Update an existing product type.'
        form_class = ProductTypeForm

    @classmethod
    def get_form_kwargs(cls, root, info, **input):
        kwargs = super().get_form_kwargs(root, info, **input)
        product_attributes = input.pop('product_attributes', None)
        if product_attributes is not None:
            product_attributes = {
                get_node(info, pr_att_id, only_type=ProductAttribute)
                for pr_att_id in product_attributes}
        else:
            product_attributes = kwargs.get(
                'instance').product_attributes.all()
        kwargs['data']['product_attributes'] = product_attributes

        variant_attributes = input.pop('variant_attributes', None)
        if variant_attributes is not None:
            variant_attributes = {
                get_node(info, pr_att_id, only_type=ProductAttribute)
                for pr_att_id in variant_attributes}
        else:
            variant_attributes = kwargs.get(
                'instance').variant_attributes.all()
        kwargs['data']['variant_attributes'] = variant_attributes

        return kwargs


class ProductTypeDeleteMutation(StaffMemberRequiredMixin, ModelDeleteMutation):
    permissions = 'product.edit_properties'

    class Meta:
        description = 'Deletes a product type.'
        model = models.ProductType
