import graphene

from ....core.permissions import ProductPermissions
from ....product import models
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types.common import ProductError


class AttributeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of attribute IDs to delete."
        )

    class Meta:
        description = "Deletes attributes."
        model = models.Attribute
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"


class AttributeValueBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description="List of attribute value IDs to delete.",
        )

    class Meta:
        description = "Deletes values of attributes."
        model = models.AttributeValue
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
