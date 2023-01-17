import graphene

from ....core.permissions import OrderPermissions
from ....order import models
from ....order.actions import cancel_order
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import BaseBulkMutation
from ...core.types import NonNullList, OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..mutations.order_cancel import clean_order_cancel
from ..types import Order


class OrderBulkCancel(BaseBulkMutation):
    class Arguments:
        ids = NonNullList(
            graphene.ID, required=True, description="List of orders IDs to cancel."
        )

    class Meta:
        description = "Cancels orders."
        model = models.Order
        object_type = Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_instance(cls, _info: ResolveInfo, instance) -> None:
        clean_order_cancel(instance)

    @classmethod
    def bulk_action(cls, info: ResolveInfo, queryset, /) -> None:
        manager = get_plugin_manager_promise(info.context).get()
        for order in queryset:
            cancel_order(
                order=order,
                user=info.context.user,
                app=get_app_promise(info.context).get(),
                manager=manager,
            )
