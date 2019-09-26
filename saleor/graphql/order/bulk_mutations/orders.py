import graphene

from ....order import events, models
from ....order.actions import cancel_order
from ...core.mutations import BaseBulkMutation
from ...core.types.common import OrderError
from ..mutations.orders import clean_order_cancel


class OrderBulkCancel(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID, required=True, description="List of orders IDs to cancel."
        )
        restock = graphene.Boolean(
            required=True, description="Determine if lines will be restocked or not."
        )

    class Meta:
        description = "Cancels orders."
        model = models.Order
        permissions = ("order.manage_orders",)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def clean_instance(cls, info, instance):
        clean_order_cancel(instance)

    @classmethod
    def perform_mutation(cls, root, info, ids, **data):
        data["user"] = info.context.user
        return super().perform_mutation(root, info, ids, **data)

    @classmethod
    def bulk_action(cls, queryset, user, restock):
        for order in queryset:
            cancel_order(order=order, user=user, restock=restock)
            if restock:
                events.fulfillment_restocked_items_event(
                    order=order, user=user, fulfillment=order
                )
