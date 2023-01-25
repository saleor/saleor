import graphene

from ....permission.enums import ProductPermissions
from ....product import models
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import NonNullList, ProductError
from ..types import ProductMedia


class ProductMediaBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description="List of product media IDs to delete.",
        )

    class Meta:
        description = "Deletes product media."
        model = models.ProductMedia
        object_type = ProductMedia
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
