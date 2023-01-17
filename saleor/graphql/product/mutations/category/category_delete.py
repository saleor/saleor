import graphene

from .....core.permissions import ProductPermissions
from .....product import models
from .....product.utils import delete_categories
from ....core import ResolveInfo
from ....core.mutations import ModelDeleteMutation
from ....core.types import ProductError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Category


class CategoryDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a category to delete.")

    class Meta:
        description = "Deletes a category."
        model = models.Category
        object_type = Category
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        instance = cls.get_node_or_error(info, id, only_type=Category)

        db_id = instance.id
        manager = get_plugin_manager_promise(info.context).get()
        delete_categories([db_id], manager=manager)

        instance.id = db_id
        return cls.success_response(instance)
