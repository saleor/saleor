import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....core.permissions import OrderPermissions
from ....core.tracing import traced_atomic_transaction
from ....order import OrderStatus, models
from ....order.actions import order_captured, order_confirmed
from ....order.error_codes import OrderErrorCode
from ....order.fetch import fetch_order_info
from ....payment import PaymentError, gateway
from ....payment.gateway import request_charge_action
from ...app.dataloaders import load_app
from ...core.mutations import ModelMutation
from ...core.types import OrderError
from ...plugins.dataloaders import load_plugin_manager
from ...site.dataloaders import load_site
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
    def get_instance(cls, info, **data):
        instance = super().get_instance(info, **data)
        if not instance.is_unconfirmed():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to an order with status "
                        "different than unconfirmed.",
                        code=OrderErrorCode.INVALID,
                    )
                }
            )
        if not instance.lines.exists():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Provided order id belongs to an order without products.",
                        code=OrderErrorCode.INVALID,
                    )
                }
            )
        return instance

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(cls, root, info, **data):
        order = cls.get_instance(info, **data)
        order.status = OrderStatus.UNFULFILLED
        order.save(update_fields=["status", "updated_at"])
        order_info = fetch_order_info(order)
        payment = order_info.payment
        manager = load_plugin_manager(info.context)
        app = load_app(info.context)

        if payment_transactions := list(order.payment_transactions.all()):
            try:
                # We use the last transaction as we don't have a possibility to
                # provide way of handling multiple transaction here
                payment_transaction = payment_transactions[-1]
                request_charge_action(
                    transaction=payment_transaction,
                    manager=manager,
                    charge_value=payment_transaction.authorized_value,
                    channel_slug=order.channel.slug,
                    user=info.context.user,
                    app=app,
                )
            except PaymentError as e:
                raise ValidationError(
                    str(e),
                    code=OrderErrorCode.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK,
                )
        elif payment and payment.is_authorized and payment.can_capture():
            gateway.capture(payment, manager, channel_slug=order.channel.slug)
            site = load_site(info.context)
            transaction.on_commit(
                lambda: order_captured(
                    order_info,
                    info.context.user,
                    app,
                    payment.total,
                    payment,
                    manager,
                    site.settings,
                )
            )
        transaction.on_commit(
            lambda: order_confirmed(
                order,
                info.context.user,
                app,
                manager,
                send_confirmation_email=True,
            )
        )
        return OrderConfirm(order=order)
