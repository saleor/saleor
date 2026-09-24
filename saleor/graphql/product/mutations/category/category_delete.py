import graphene

from .....permission.enums import ProductPermissions
from .....product import models
from .....product.utils import delete_categories
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_324
from ....core.mutations import ModelDeleteMutation, ModelWithExtRefMutation
from ....core.types import ProductError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Category


class CategoryDelete(ModelDeleteMutation, ModelWithExtRefMutation):
    class Arguments:
        id = graphene.ID(required=False, description="ID of a category to delete.")
        external_reference = graphene.String(
            required=False,
            description=f"External ID of a category to delete.{ADDED_IN_324}",
        )

    class Meta:
        description = "Deletes a category."
        model = models.Category
        object_type = Category
        permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, external_reference=None, id=None
    ):
        instance = cls.get_instance(info, external_reference=external_reference, id=id)

        db_id = instance.id
        manager = get_plugin_manager_promise(info.context).get()
        delete_categories([db_id], manager=manager)

        instance.id = db_id
        return cls.success_response(instance)
