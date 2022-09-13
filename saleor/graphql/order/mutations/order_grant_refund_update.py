import graphene
from django.core.exceptions import ValidationError

from ....core.permissions import OrderPermissions
from ...core.enums import OrderGrandRefundUpdateErrorCode
from ...core.mutations import BaseMutation
from ...core.scalars import Decimal
from ...core.types.common import OrderGrantRefundUpdateError
from ..types import Order, OrderGrantedRefund


class OrderGrandRefundUpdateInput(graphene.InputObjectType):
    amount = Decimal(description="Amount of the granted refund.")
    reason = graphene.String(description="Reason of the granted refund.")


class OrderGrantRefundUpdate(BaseMutation):
    order = graphene.Field(
        Order, description="Order which has assigned updated grant refund."
    )
    granted_refund = graphene.Field(
        OrderGrantedRefund, description="Created granted refund."
    )

    class Arguments:
        id = graphene.ID(description="ID of the granted refund.", required=True)
        input = OrderGrandRefundUpdateInput(
            required=True,
            description="Fields required to update a granted refund.",
        )

    class Meta:
        description = "Updates granted refund."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderGrantRefundUpdateError
        error_type_field = "order_errors"

    @classmethod
    def validate_input(cls, amount, reason):
        if not amount and not reason:
            error_msg = (
                "At least amount or reason need to be provided to process update."
            )
            raise ValidationError(
                {
                    "input": ValidationError(
                        error_msg, code=OrderGrandRefundUpdateErrorCode.REQUIRED.value
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        granted_refund = cls.get_node_or_error(
            info, data["id"], only_type=OrderGrantedRefund
        )
        amount = data["input"].get("amount")
        reason = data["input"].get("reason")
        cls.validate_input(amount, reason)
        amount = amount if amount is not None else granted_refund.amount_value
        reason = reason if reason is not None else granted_refund.reason
        granted_refund.amount_value = amount
        granted_refund.reason = reason
        granted_refund.save(update_fields=["amount_value", "reason", "updated_at"])
        return cls(order=granted_refund.order, granted_refund=granted_refund)
