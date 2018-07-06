import graphene

from ....product import models
from ...core.mutations import ModelDeleteMutation, ModelMutation


class ProductAttributesInput(graphene.InputObjectType):
    slug = graphene.String(
        required=True, description='Internal name.')
    name = graphene.String(
        required=True, description='Name displayed in the interface.')


class AttributeChoiceValueInput(graphene.InputObjectType):
    attribute = graphene.ID(
        required=False,
        description='Attribute to which value will be assigned.')
    slug = graphene.String(
        required=True, description='Internal name.')
    name = graphene.String(
        required=True, description='Name displayed in the interface.')


class AttributeChoiceValueUpdateInput(graphene.InputObjectType):
    slug = graphene.String(
        required=True, description='Internal name.')
    name = graphene.String(
        required=True, description='Name displayed in the interface.')


class ProductAttributeCreate(ModelMutation):
    class Arguments:
        input = ProductAttributesInput(
            required=True,
            description='Fields required to create a product attribute.')

    class Meta:
        description = 'Creates a product attribute.'
        model = models.ProductAttribute

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.edit_product')


class ProductAttributeUpdate(ProductAttributeCreate):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a product attribute to update.')
        input = ProductAttributesInput(
            required=True,
            description='Fields required to update a product attribute.')

    class Meta:
        description = 'Updates a product attribute.'
        model = models.ProductAttribute


class ProductAttributeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of a product attribute to delete.')

    class Meta:
        description = 'Deletes a product attribute.'
        model = models.ProductAttribute

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.edit_product')


class AttributeChoiceValueCreate(ModelMutation):
    class Arguments:
        input = AttributeChoiceValueInput(
            required=True,
            description='Fields required to create an attribute choice value.')

    class Meta:
        description = 'Creates an attribute choice value.'
        model = models.AttributeChoiceValue

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.edit_product')


class AttributeChoiceValueUpdate(AttributeChoiceValueCreate):
    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of an attribute choice value to update.')
        input = AttributeChoiceValueUpdateInput(
            required=True,
            description='Fields required to update an attribute choice value.')

    class Meta:
        description = 'Updates an attribute choice value.'
        model = models.AttributeChoiceValue


class AttributeChoiceValueDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of an attribute choice value to delete.')

    class Meta:
        description = 'Deletes an attribute choice value.'
        model = models.AttributeChoiceValue

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.edit_product')
