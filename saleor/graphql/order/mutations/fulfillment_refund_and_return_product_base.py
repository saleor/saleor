from typing import Optional

import graphene
from django.core.exceptions import ValidationError

from ....giftcard.utils import order_has_gift_card_lines
from ....order import FulfillmentLineData
from ....order import models as order_models
from ....order.error_codes import OrderErrorCode
from ....order.fetch import OrderLineInfo
from ....payment.models import TransactionItem
from ...core.mutations import BaseMutation
from ..types import FulfillmentLine, OrderLine


class FulfillmentRefundAndReturnProductBase(BaseMutation):
    class Meta:
        abstract = True

    @classmethod
    def clean_order_payment(cls, payment, cleaned_input):
        if not payment or not payment.can_refund():
            raise ValidationError(
                {
                    "order": ValidationError(
                        "Order cannot be refunded.",
                        code=OrderErrorCode.CANNOT_REFUND.value,
                    )
                }
            )
        cleaned_input["payment"] = payment

    @classmethod
    def clean_amount_to_refund(
        cls, order, amount_to_refund, charged_value, cleaned_input
    ):
        if amount_to_refund is not None:
            if order_has_gift_card_lines(order):
                raise ValidationError(
                    {
                        "amount_to_refund": ValidationError(
                            (
                                "Cannot specified amount to refund when order has "
                                "gift card lines."
                            ),
                            code=OrderErrorCode.CANNOT_REFUND.value,
                        )
                    }
                )

            if amount_to_refund > charged_value:
                raise ValidationError(
                    {
                        "amount_to_refund": ValidationError(
                            (
                                "The amountToRefund is greater than the maximal "
                                "possible amount to refund."
                            ),
                            code=OrderErrorCode.CANNOT_REFUND.value,
                        ),
                    }
                )
        cleaned_input["amount_to_refund"] = amount_to_refund

    @classmethod
    def _raise_error_for_line(cls, msg, type, line_id, field_name, code=None):
        line_global_id = graphene.Node.to_global_id(type, line_id)
        if not code:
            code = OrderErrorCode.INVALID_QUANTITY.value
        raise ValidationError(
            {
                field_name: ValidationError(
                    msg,
                    code=code,
                    params={field_name: line_global_id},
                )
            }
        )

    @classmethod
    def raise_error_for_payment_error(cls, transactions: Optional[TransactionItem]):
        if transactions:
            code = OrderErrorCode.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.value
            msg = "No app or plugin is configured to handle payment action requests."
        else:
            msg = "The refund operation is not available yet."
            code = OrderErrorCode.CANNOT_REFUND.value
        raise ValidationError(
            msg,
            code=code,
        )

    @classmethod
    def clean_fulfillment_lines(
        cls, fulfillment_lines_data, cleaned_input, whitelisted_statuses
    ):
        fulfillment_lines = cls.get_nodes_or_error(
            [line["fulfillment_line_id"] for line in fulfillment_lines_data],
            field="fulfillment_lines",
            only_type=FulfillmentLine,
            qs=order_models.FulfillmentLine.objects.prefetch_related(
                "fulfillment", "order_line"
            ),
        )
        fulfillment_lines = list(fulfillment_lines)
        cleaned_fulfillment_lines = []
        for line, line_data in zip(fulfillment_lines, fulfillment_lines_data):
            quantity = line_data["quantity"]
            if line.order_line.is_gift_card:
                cls._raise_error_for_line(
                    "Cannot refund or return gift card line.",
                    "FulfillmentLine",
                    line.pk,
                    "fulfillment_line_id",
                    OrderErrorCode.GIFT_CARD_LINE.value,
                )
            if line.quantity < quantity:
                cls._raise_error_for_line(
                    "Provided quantity is bigger than quantity from "
                    "fulfillment line",
                    "FulfillmentLine",
                    line.pk,
                    "fulfillment_line_id",
                )
            if line.fulfillment.status not in whitelisted_statuses:
                allowed_statuses_str = ", ".join(whitelisted_statuses)
                cls._raise_error_for_line(
                    f"Unable to process action for fulfillmentLine with different "
                    f"status than {allowed_statuses_str}.",
                    "FulfillmentLine",
                    line.pk,
                    "fulfillment_line_id",
                    code=OrderErrorCode.INVALID.value,
                )
            replace = line_data.get("replace", False)
            if replace and not line.order_line.variant_id:
                cls._raise_error_for_line(
                    "Unable to replace line as the assigned product doesn't exist.",
                    "OrderLine",
                    line.pk,
                    "order_line_id",
                )
            cleaned_fulfillment_lines.append(
                FulfillmentLineData(
                    line=line,
                    quantity=quantity,
                    replace=replace,
                )
            )
        cleaned_input["fulfillment_lines"] = cleaned_fulfillment_lines

    @classmethod
    def clean_lines(cls, lines_data, cleaned_input):
        order_lines = cls.get_nodes_or_error(
            [line["order_line_id"] for line in lines_data],
            field="order_lines",
            only_type=OrderLine,
            qs=order_models.OrderLine.objects.prefetch_related(
                "fulfillment_lines__fulfillment", "variant", "allocations"
            ),
        )
        order_lines = list(order_lines)
        cleaned_order_lines = []
        for line, line_data in zip(order_lines, lines_data):
            quantity = line_data["quantity"]
            if line.is_gift_card:
                cls._raise_error_for_line(
                    "Cannot refund or return gift card line.",
                    "OrderLine",
                    line.pk,
                    "order_line_id",
                    OrderErrorCode.GIFT_CARD_LINE.value,
                )
            if line.quantity < quantity:
                cls._raise_error_for_line(
                    "Provided quantity is bigger than quantity from order line.",
                    "OrderLine",
                    line.pk,
                    "order_line_id",
                )
            quantity_ready_to_move = line.quantity_unfulfilled
            if quantity_ready_to_move < quantity:
                cls._raise_error_for_line(
                    "Provided quantity is bigger than unfulfilled quantity.",
                    "OrderLine",
                    line.pk,
                    "order_line_id",
                )
            variant = line.variant
            replace = line_data.get("replace", False)
            if replace and not line.variant_id:
                cls._raise_error_for_line(
                    "Unable to replace line as the assigned product doesn't exist.",
                    "OrderLine",
                    line.pk,
                    "order_line_id",
                )

            cleaned_order_lines.append(
                OrderLineInfo(
                    line=line, quantity=quantity, variant=variant, replace=replace
                )
            )
        cleaned_input["order_lines"] = cleaned_order_lines
