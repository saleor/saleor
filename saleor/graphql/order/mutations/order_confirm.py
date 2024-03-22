from typing import cast

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....account.models import User
from ....core.tracing import traced_atomic_transaction
from ....order import OrderStatus, models
from ....order.actions import order_charged, order_confirmed
from ....order.error_codes import OrderErrorCode
from ....order.fetch import fetch_order_info
from ....order.utils import update_order_display_gross_prices
from ....payment import PaymentError, TransactionAction, gateway
from ....payment.gateway import request_charge_action
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.mutations import ModelMutation
from ...core.types import OrderError
from ...payment.mutations.transaction.utils import create_transaction_event_requested
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

    @staticmethod
    def charge_transaction_items(user, app, order, manager):
        already_charged_amount = 0
        transaction_items = order.payment_transactions.all()
        for transaction_item in transaction_items:
            if transaction_item.amount_charged:
                already_charged_amount += transaction_item.amount_charged

        for transaction_item in transaction_items:
            if (
                not transaction_item.authorized_value > 0
                or TransactionAction.CHARGE not in transaction_item.available_actions
            ):
                continue
            charge_value = (
                min(transaction_item.authorized_value, order.total.gross.amount)
                - already_charged_amount
            )
            if charge_value <= 0:
                return
            event = create_transaction_event_requested(
                transaction_item,
                charge_value,
                TransactionAction.CHARGE,
                user=user,
                app=app,
            )
            try:
                request_charge_action(
                    channel_slug=order.channel.slug,
                    user=user,
                    app=app,
                    transaction=transaction_item,
                    manager=manager,
                    charge_value=charge_value,
                    request_event=event,
                )
            except PaymentError:
                continue
            already_charged_amount += charge_value

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        user = info.context.user
        user = cast(User, user)
        order = cls.get_instance(info, **data)
        cls.check_channel_permissions(info, [order.channel_id])
        order.status = OrderStatus.UNFULFILLED
        update_order_display_gross_prices(order)
        order.save(update_fields=["status", "updated_at", "display_gross_prices"])
        order_info = fetch_order_info(order)
        payment = order_info.payment
        manager = get_plugin_manager_promise(info.context).get()
        app = get_app_promise(info.context).get()
        with traced_atomic_transaction():
            if payment and payment.is_authorized and payment.can_capture():
                authorized_payment = payment
                gateway.capture(payment, manager, channel_slug=order.channel.slug)
                site = get_site_promise(info.context).get()
                transaction.on_commit(
                    lambda: order_charged(
                        order_info,
                        info.context.user,
                        app,
                        authorized_payment.total,
                        authorized_payment,
                        manager,
                        site.settings,
                    )
                )
            cls.charge_transaction_items(user, app, order, manager)
            transaction.on_commit(
                lambda: order_confirmed(
                    order,
                    user,
                    app,
                    manager,
                    send_confirmation_email=True,
                )
            )
        return OrderConfirm(order=order)
