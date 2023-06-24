from typing import cast

from django.core.exceptions import ValidationError

from .....order import models as order_models
from .....order.actions import order_refunded
from .....payment import PaymentError, TransactionKind, gateway
from .....payment.error_codes import PaymentErrorCode
from .....permission.enums import OrderPermissions
from ....app.dataloaders import get_app_promise
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_PAYMENTS
from ....core.types import common as common_types
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Payment
from .payment_capture import PaymentCapture


class PaymentRefund(PaymentCapture):
    class Meta:
        description = "Refunds the captured payment amount."
        doc_category = DOC_CATEGORY_PAYMENTS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = common_types.PaymentError
        error_type_field = "payment_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, amount=None, payment_id
    ):
        app = get_app_promise(info.context).get()
        user = info.context.user
        manager = get_plugin_manager_promise(info.context).get()

        payment = cls.get_node_or_error(
            info, payment_id, field="payment_id", only_type=Payment
        )
        channel = payment.order.channel if payment.order else payment.checkout.channel
        cls.check_channel_permissions(info, [channel.id])
        channel_slug = channel.slug
        manager = get_plugin_manager_promise(info.context).get()
        payment_transaction = None
        try:
            payment_transaction = gateway.refund(
                payment,
                manager,
                amount=amount,
                channel_slug=channel_slug,
            )
            payment.refresh_from_db()
        except PaymentError as e:
            raise ValidationError(str(e), code=PaymentErrorCode.PAYMENT_ERROR.value)
        if (
            payment.order_id
            and payment_transaction
            and payment_transaction.kind == TransactionKind.REFUND
        ):
            order = cast(order_models.Order, payment.order)
            order_refunded(
                order=order,
                user=user,
                app=app,
                amount=amount,
                payment=payment,
                manager=manager,
            )
        return PaymentRefund(payment=payment)
