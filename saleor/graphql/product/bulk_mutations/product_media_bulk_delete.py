import graphene
from django.conf import settings

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
            description=(
                "List of product media IDs to delete. The number of items is "
                f"limited to {settings.BULK_DELETE_LIMIT} by default. Exceeding the limit returns an `INVALID` error."
            ),
        )

    class Meta:
        description = "Deletes product media."
        model = models.ProductMedia
        object_type = ProductMedia
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
        max_input_size = settings.BULK_DELETE_LIMIT
