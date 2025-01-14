import graphene
from django.core.exceptions import ValidationError

from ....order.actions import order_charged
from ....order.error_codes import OrderErrorCode
from ....order.fetch import fetch_order_info
from ....payment import TransactionKind, gateway
from ....payment import models as payment_models
from ....permission.enums import OrderPermissions
from ...app.dataloaders import get_app_promise
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.scalars import PositiveDecimal
from ...core.types import OrderError
from ...plugins.dataloaders import get_plugin_manager_promise
from ...site.dataloaders import get_site_promise
from ..types import Order
from .utils import clean_payment, try_payment_action


def clean_order_capture(
    payment: payment_models.Payment | None,
) -> payment_models.Payment:
    payment = clean_payment(payment)
    if not payment.is_active:
        raise ValidationError(
            {
                "payment": ValidationError(
                    "Only pre-authorized payments can be captured",
                    code=OrderErrorCode.CAPTURE_INACTIVE_PAYMENT.value,
                )
            }
        )
    return payment


class OrderCapture(BaseMutation):
    order = graphene.Field(Order, description="Captured order.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the order to capture.")
        amount = PositiveDecimal(
            required=True, description="Amount of money to capture."
        )

    class Meta:
        description = "Capture an order."
        doc_category = DOC_CATEGORY_ORDERS
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderError
        error_type_field = "order_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, amount, id: str
    ):
        if amount <= 0:
            raise ValidationError(
                {
                    "amount": ValidationError(
                        "Amount should be a positive number.",
                        code=OrderErrorCode.ZERO_QUANTITY.value,
                    )
                }
            )

        order = cls.get_node_or_error(info, id, only_type=Order)
        cls.check_channel_permissions(info, [order.channel_id])

        app = get_app_promise(info.context).get()
        manager = get_plugin_manager_promise(info.context).get()
        order_info = fetch_order_info(order)
        payment = order_info.payment
        payment = clean_order_capture(payment)
        transaction = try_payment_action(
            order,
            info.context.user,
            app,
            payment,
            gateway.capture,
            payment,
            manager,
            amount=amount,
            channel_slug=order.channel.slug,
        )
        payment.refresh_from_db()
        # Confirm that we changed the status to capture. Some payment can receive
        # asynchronous webhook with update status
        if transaction.kind == TransactionKind.CAPTURE:
            site = get_site_promise(info.context).get()
            order_charged(
                order_info,
                info.context.user,
                app,
                amount,
                payment,
                manager,
                site.settings,
            )
        return OrderCapture(order=order)
