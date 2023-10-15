from typing import cast

import graphene

from ....account.models import User
from ....order.actions import fulfillment_tracking_updated
from ....order.notifications import send_fulfillment_update
from ....permission.enums import OrderPermissions
from ....webhook.event_types import WebhookEventAsyncType
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import OrderError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Fulfillment, Order
from .order_fulfill import FulfillmentUpdateTrackingInput


class FulfillmentUpdateTracking(BaseMutation):
    fulfillment = graphene.Field(
        Fulfillment, description="A fulfillment with updated tracking."
    )
    order = graphene.Field(
        Order, description="Order for which fulfillment was updated."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a fulfillment to update.")
        input = FulfillmentUpdateTrackingInput(
            required=True, description="Fields required to update a fulfillment."
        )

    class Meta:
        description = "Updates a fulfillment for an order."
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.FULFILLMENT_TRACKING_NUMBER_UPDATED,
                description="Fulfillment tracking number is updated.",
            )
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        id,
        input,
    ):
        user = info.context.user
        user = cast(User, user)
        fulfillment = cls.get_node_or_error(info, id, only_type=Fulfillment)

        order = fulfillment.order
        cls.check_channel_permissions(info, [order.channel_id])

        tracking_number = input.get("tracking_number") or ""
        fulfillment.tracking_number = tracking_number
        fulfillment.save()

        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        fulfillment_tracking_updated(fulfillment, user, app, tracking_number, manager)

        notify_customer = input.get("notify_customer")
        if notify_customer:
            send_fulfillment_update(order, fulfillment, manager)

        return FulfillmentUpdateTracking(fulfillment=fulfillment, order=order)
