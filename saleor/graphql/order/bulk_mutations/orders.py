import graphene

from ....core.permissions import OrderPermissions
from ....order import models
from ....order.actions import cancel_order
from ...app.dataloaders import load_app
from ...core.mutations import BaseBulkMutation
from ...core.types import NonNullList, OrderError
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
    def clean_instance(cls, info, instance):
        clean_order_cancel(instance)

    @classmethod
    def bulk_action(cls, info, queryset):
        for order in queryset:
            cancel_order(
                order=order,
                user=info.context.user,
                app=load_app(info.context),
                manager=info.context.plugins,
            )
