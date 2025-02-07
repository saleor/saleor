from typing import cast

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....account.models import User
from ....core.tracing import traced_atomic_transaction
from ....order import models
from ....order.actions import (
    WEBHOOK_EVENTS_FOR_ORDER_CHARGED,
    WEBHOOK_EVENTS_FOR_ORDER_CONFIRMED,
    order_charged,
    order_confirmed,
)
from ....order.error_codes import OrderErrorCode
from ....order.fetch import fetch_order_info
from ....order.utils import update_order_display_gross_prices, update_order_status
from ....payment import gateway
from ....permission.enums import OrderPermissions
from ....webhook.utils import get_webhooks_for_multiple_events
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...site.dataloaders import get_site_promise
from ..types import Order


class OrderConfirm(ModelMutation):
    order = graphene.Field(Order, description="Order which has been confirmed.")

    class Arguments:
        id = graphene.ID(description="ID of an order to confirm.", required=True)

    class Meta:
        description = "Confirms an unconfirmed order by changing status to unfulfilled."
        model = models.Order
        object_type = Order
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def get_instance(cls, info: ResolveInfo, **data):
        instance = super().get_instance(info, **data)
        if not instance.is_unconfirmed():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to an order with status "
                        "different than unconfirmed.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )
        if not instance.lines.exists():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to an order without products.",
                        code=OrderErrorCode.INVALID.value,
                    )
                }
            )
        return instance

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        user = info.context.user
        user = cast(User, user)
        order = cls.get_instance(info, **data)
        cls.check_channel_permissions(info, [order.channel_id])
        update_order_status(order)
        update_order_display_gross_prices(order)
        order.save(update_fields=["updated_at", "display_gross_prices"])
        order_info = fetch_order_info(order)
        payment = order_info.payment
        manager = get_plugin_manager_promise(info.context).get()
        app = get_app_promise(info.context).get()
        webhook_events = WEBHOOK_EVENTS_FOR_ORDER_CONFIRMED
        webhook_event_map = None
        with traced_atomic_transaction():
            if payment and payment.is_authorized and payment.can_capture():
                authorized_payment = payment
                gateway.capture(payment, manager, channel_slug=order.channel.slug)
                site = get_site_promise(info.context).get()
                webhook_events = webhook_events.union(WEBHOOK_EVENTS_FOR_ORDER_CHARGED)
                webhook_event_map = get_webhooks_for_multiple_events(webhook_events)
                transaction.on_commit(
                    lambda: order_charged(
                        order_info,
                        user,
                        app,
                        authorized_payment.total,
                        authorized_payment,
                        manager,
                        site.settings,
                        payment.gateway,
                        webhook_event_map=webhook_event_map,
                    )
                )
            if webhook_event_map is None:
                webhook_event_map = get_webhooks_for_multiple_events(webhook_events)

            transaction.on_commit(
                lambda: order_confirmed(
                    order,
                    user,
                    app,
                    manager,
                    send_confirmation_email=True,
                    webhook_event_map=webhook_event_map,
                )
            )
        return OrderConfirm(order=order)
