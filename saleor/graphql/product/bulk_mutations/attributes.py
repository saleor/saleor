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
        permissions = ('product.manage_products', )


class AttributeValueBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of attribute value IDs to delete.')

    class Meta:
        description = 'Deletes values of attributes.'
        model = models.AttributeValue
        permissions = ('product.manage_products', )
