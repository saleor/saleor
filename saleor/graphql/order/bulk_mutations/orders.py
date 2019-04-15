import graphene

from ....order import OrderEvents, models
from ....order.utils import cancel_order
from ...core.mutations import BaseBulkMutation
from ..mutations.orders import clean_order_cancel


class OrdersCancel(BaseBulkMutation):
    class Arguments:
        ids = graphene.List(
            graphene.ID,
            required=True,
            description='List of orders IDs to cancel.')
        restock = graphene.Boolean(
            required=True,
            description='Determine if lines will be restocked or not.')

    class Meta:
        description = 'Cancels orders.'
        model = models.Order

    @classmethod
    def clean_instance(cls, info, instance):
        clean_order_cancel(instance)

    @classmethod
    def user_is_allowed(cls, user, input):
        return user.has_perm('order.manage_orders')

    @classmethod
    def bulk_action(cls, instances, user, restock):
        for order in instances:
            cancel_order(order=order, restock=restock)
            if restock:
                order.events.create(
                    type=OrderEvents.FULFILLMENT_RESTOCKED_ITEMS.value,
                    user=user,
                    parameters={'quantity': order.get_total_quantity()})
            else:
                order.events.create(
                    type=OrderEvents.CANCELED.value, user=user)
