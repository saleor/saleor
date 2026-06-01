import graphene
from django.conf import settings

from ....permission.enums import ProductPermissions
from ....product import models
from ....product.utils import delete_categories
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import NonNullList, ProductError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Category


class CategoryBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID,
            required=True,
            description=(
                "List of category IDs to delete. The number of items is limited. "
                "Exceeding the limit returns an `INVALID` error."
            ),
        )

    class Meta:
        description = "Deletes categories."
        model = models.Category
        object_type = Category
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"
        max_input_size = settings.BULK_DELETE_LIMIT

    @classmethod
    def bulk_action(cls, info, queryset):
        manager = get_plugin_manager_promise(info.context).get()
        delete_categories(queryset.values_list("pk", flat=True), manager)
