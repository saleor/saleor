import graphene

from ....core.permissions import ProductPermissions
from ....product import models
from ....product.utils import delete_categories
from ...core.mutations import ModelBulkDeleteMutation
from ...core.types import NonNullList, ProductError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Category


class CategoryBulkDelete(ModelBulkDeleteMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of category IDs to delete."
        )

    class Meta:
        description = "Deletes categories."
        model = models.Category
        object_type = Category
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def bulk_action(cls, info, queryset):
        manager = load_plugin_manager(info.context)
        delete_categories(queryset.values_list("pk", flat=True), manager)
