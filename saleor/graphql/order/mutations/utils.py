from django.core.exceptions import ValidationError

from ....order import OrderStatus, events
from ....order.error_codes import OrderErrorCode
from ....payment import PaymentError
from ....plugins.manager import PluginsManager
from ....shipping.interface import ShippingMethodData
from ..utils import get_shipping_method_availability_error

ORDER_EDITABLE_STATUS = (OrderStatus.DRAFT, OrderStatus.UNCONFIRMED)


class EditableOrderValidationMixin:
    class Meta:
        abstract = True

    @classmethod
    def validate_order(cls, order):
        if order.status not in ORDER_EDITABLE_STATUS:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Only draft and unconfirmed orders can be edited.",
                        code=OrderErrorCode.NOT_EDITABLE,
                    )
                }
            )


def clean_order_update_shipping(
    order, method: ShippingMethodData, manager: "PluginsManager"
):
    if not order.shipping_address:
        raise ValidationError(
            {
                "order": ValidationError(
                    "Cannot choose a shipping method for an order without "
                    "the shipping address.",
                    code=OrderErrorCode.ORDER_NO_SHIPPING_ADDRESS.value,
                )
            }
        )

    error = get_shipping_method_availability_error(order, method, manager)
    if error:
        raise ValidationError({"shipping_method": error})


def get_webhook_handler_by_order_status(status, info):
    if status == OrderStatus.DRAFT:
        return info.context.plugins.draft_order_updated
    else:
        return info.context.plugins.order_updated


def try_payment_action(order, user, app, payment, func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
        # provided order might alter it's total_paid.
        order.refresh_from_db()
        return result
    except (PaymentError, ValueError) as e:
        message = str(e)
        events.payment_failed_event(
            order=order, user=user, app=app, message=message, payment=payment
        )
        raise ValidationError(
            {"payment": ValidationError(message, code=OrderErrorCode.PAYMENT_ERROR)}
        )


def clean_payment(payment):
    if not payment:
        raise ValidationError(
            {
                "payment": ValidationError(
                    "There's no payment associated with the order.",
                    code=OrderErrorCode.PAYMENT_MISSING,
                )
            }
        )
