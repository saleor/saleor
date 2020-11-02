import graphene

from ...attribute import models
from ...core.permissions import PageTypePermissions
from ..core.mutations import ModelBulkDeleteMutation
from ..core.types.common import AttributeError


class AttributeBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of attribute IDs to delete."
        )

    class Meta:
        description = "Deletes attributes."
        model = models.Attribute
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"


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
        permissions = (PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"
