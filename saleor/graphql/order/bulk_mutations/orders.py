import graphene

from ....core.permissions import OrderPermissions
from ....order import models
from ....order.actions import cancel_order
from ...core.mutations import BaseBulkMutation
from ...core.types.common import OrderError
from ...utils import get_user_or_app_from_context
from ..mutations.orders import clean_order_cancel


class OrderBulkCancel(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of orders IDs to cancel."
        )

    class Meta:
        description = "Cancels orders."
        model = models.Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_instance(cls, info, instance):
        clean_order_cancel(instance)

    @classmethod
    def perform_mutation(cls, root, info, ids, **data):
        data["user"] = get_user_or_app_from_context(info.context)
        return super().perform_mutation(root, info, ids, **data)

    @classmethod
    def bulk_action(cls, queryset, user):
        for order in queryset:
            cancel_order(order=order, user=user)
