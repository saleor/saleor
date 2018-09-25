import graphene

from ....product import models
from ...core.mutations import ModelDeleteMutation, ModelMutation


class AttributesInput(graphene.InputObjectType):
    slug = graphene.String(
        required=True, description='Internal name.')
    name = graphene.String(
        required=True, description='Name displayed in the interface.')


class AttributeValueCreateInput(graphene.InputObjectType):
    attribute = graphene.ID(
        required=False,
        description='Attribute to which value will be assigned.',
        name='attribute')
    slug = graphene.String(
        required=True, description='Internal name.')
    name = graphene.String(
        required=True, description='Name displayed in the interface.')
    value = graphene.String(
        required=True, description='Real value eg. HEX color.')


class AttributeValueUpdateInput(graphene.InputObjectType):
    slug = graphene.String(
        required=True, description='Internal name.')
    name = graphene.String(
        required=True, description='Name displayed in the interface.')


class AttributeCreate(ModelMutation):
    class Arguments:
        input = AttributesInput(
            required=True,
            description='Fields required to create an attribute.')

    class Meta:
        description = 'Creates an attribute.'
        model = models.Attribute

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')


class AttributeUpdate(AttributeCreate):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an attribute to update.')
        input = AttributesInput(
            required=True,
            description='Fields required to update an attribute.')

    class Meta:
        description = 'Updates anattribute.'
        model = models.Attribute


class AttributeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True, description='ID of an attribute to delete.')

    class Meta:
        description = 'Deletes an attribute.'
        model = models.Attribute

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')


class AttributeValueCreate(ModelMutation):
    class Arguments:
        input = AttributeValueCreateInput(
            required=True,
            description='Fields required to create an attribute choice value.')

    class Meta:
        description = 'Creates an attribute choice value.'
        model = models.AttributeValue

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')


class AttributeValueUpdate(AttributeValueCreate):
    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of an attribute choice value to update.')
        input = AttributeValueUpdateInput(
            required=True,
            description='Fields required to update an attribute choice value.')

    class Meta:
        description = 'Updates an attribute choice value.'
        model = models.AttributeValue


class AttributeValueDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(
            required=True,
            description='ID of an attribute choice value to delete.')

    class Meta:
        description = 'Deletes an attribute choice value.'
        model = models.AttributeValue

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')
