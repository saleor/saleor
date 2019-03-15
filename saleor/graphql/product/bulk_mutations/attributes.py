import graphene

from ....product import models
from ...core.mutations import ModelBulkDeleteMutation


class AttributeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of attribute IDs to delete.')

    class Meta:
        description = 'Deletes attributes.'
        model = models.Attribute

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')


class AttributeValueBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of attribute value IDs to delete.')

    class Meta:
        description = 'Deletes values of attributes.'
        model = models.AttributeValue

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('product.manage_products')
