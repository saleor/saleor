import graphene

from ....core.tracing import traced_atomic_transaction
from ....discount import models
from ....discount.utils import fetch_catalogue_info
from ....graphql.core.mutations import ModelDeleteMutation
from ....permission.enums import DiscountPermissions
from ...core import ResolveInfo
from ...core.types import DiscountError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Sale
from .sale_create import SaleUpdateDiscountedPriceMixin
from .utils import convert_catalogue_info_to_global_ids


class SaleDelete(SaleUpdateDiscountedPriceMixin, ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a sale to delete.")

    class Meta:
        description = "Deletes a sale."
        model = models.Sale
        object_type = Sale
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, root, info: ResolveInfo, /, *, id: str
    ):
        instance = cls.get_node_or_error(info, id, only_type=Sale)
        previous_catalogue = fetch_catalogue_info(instance)
        manager = get_plugin_manager_promise(info.context).get()
        with traced_atomic_transaction():
            response = super().perform_mutation(root, info, id=id)
            cls.call_event(
                lambda: manager.sale_deleted(
                    instance, convert_catalogue_info_to_global_ids(previous_catalogue)
                )
            )
        return response
