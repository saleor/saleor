import decimal
from typing import Any, Optional, Union

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....order import models
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_313, ADDED_IN_315, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.scalars import Decimal
from ...core.types import BaseInputObjectType
from ...core.types.common import Error, NonNullList
from ..enums import OrderGrantRefundCreateErrorCode, OrderGrantRefundCreateLineErrorCode
from ..types import Order, OrderGrantedRefund
from .order_grant_refund_utils import (
    assign_order_lines,
    get_input_lines_data,
    handle_lines_with_quantity_already_refunded,
    shipping_costs_already_granted,
)


class OrderGrantRefundCreateLineError(Error):
    code = OrderGrantRefundCreateLineErrorCode(
        description="The error code.", required=True
    )
    line_id = graphene.ID(
        description="The ID of the line related to the error.", required=True
    )


class OrderGrantRefundCreateError(Error):
    code = OrderGrantRefundCreateErrorCode(description="The error code.", required=True)
    lines = NonNullList(
        OrderGrantRefundCreateLineError,
        description="List of lines which cause the error."
        + ADDED_IN_315
        + PREVIEW_FEATURE,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderGrantRefundCreateLineInput(BaseInputObjectType):
    id = graphene.ID(description="The ID of the order line.", required=True)
    quantity = graphene.Int(
        description="The quantity of line items to be marked to refund.", required=True
    )
    reason = graphene.String(description="Reason of the granted refund for the line.")

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderGrantRefundCreateInput(BaseInputObjectType):
    amount = Decimal(
        description=(
            "Amount of the granted refund. If not provided, the amount will be "
            "calculated automatically based on provided `lines` and "
            "`grantRefundForShipping`."
        )
    )
    reason = graphene.String(description="Reason of the granted refund.")
    lines = NonNullList(
        OrderGrantRefundCreateLineInput,
        description="Lines to assign to granted refund."
        + ADDED_IN_315
        + PREVIEW_FEATURE,
        required=False,
    )
    grant_refund_for_shipping = graphene.Boolean(
        description="Determine if granted refund should include shipping costs."
        + ADDED_IN_315
        + PREVIEW_FEATURE,
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderGrantRefundCreate(BaseMutation):
    order = graphene.Field(
        Order, description="Order which has assigned new grant refund."
    )
    granted_refund = graphene.Field(
        OrderGrantedRefund, description="Created granted refund."
    )

    class Arguments:
        id = graphene.ID(description="ID of the order.", required=True)
        input = OrderGrantRefundCreateInput(
            required=True,
            description="Fields required to create a granted refund for the order.",
        )

    class Meta:
        description = (
            "Adds granted refund to the order." + ADDED_IN_313 + PREVIEW_FEATURE
        )
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderGrantRefundCreateError
        doc_category = DOC_CATEGORY_ORDERS

    @classmethod
    def clean_input_lines(
        cls,
        order: models.Order,
        lines: list[dict[str, Union[str, int]]],
    ) -> tuple[list[models.OrderGrantedRefundLine], Optional[list[dict[str, str]]]]:
        errors: list[dict[str, str]] = []
        input_lines_data = get_input_lines_data(
            lines, errors, OrderGrantRefundCreateLineErrorCode.GRAPHQL_ERROR.value
        )
        assign_order_lines(
            order,
            input_lines_data,
            errors,
            OrderGrantRefundCreateLineErrorCode.NOT_FOUND.value,
        )
        handle_lines_with_quantity_already_refunded(
            order,
            input_lines_data,
            errors,
            OrderGrantRefundCreateLineErrorCode.QUANTITY_GREATER_THAN_AVAILABLE.value,
        )

        if errors:
            return [], errors

        return list(input_lines_data.values()), None

    @classmethod
    def calculate_amount(
        cls,
        order: models.Order,
        cleaned_input_lines: list[models.OrderGrantedRefundLine],
        grant_refund_for_shipping: bool,
    ) -> decimal.Decimal:
        amount = decimal.Decimal(0)
        for granted_refund_line in cleaned_input_lines:
            amount += (
                granted_refund_line.order_line.unit_price_gross_amount
                * granted_refund_line.quantity
            )
        if grant_refund_for_shipping:
            amount += order.shipping_price_gross_amount
        return amount

    @classmethod
    def validate_input(cls, input: dict[str, Any]):
        amount = input.get("amount")
        input_lines = input.get("lines", [])
        grant_refund_for_shipping = input.get("grant_refund_for_shipping", False)

        if amount is None and not input_lines and not grant_refund_for_shipping:
            error_msg = (
                "You must provide at least one of `amount`, `lines`, "
                "`grantRefundForShipping`."
            )
            error_code = OrderGrantRefundCreateErrorCode.REQUIRED.value
            raise ValidationError(
                {
                    "amount": ValidationError(error_msg, code=error_code),
                    "lines": ValidationError(error_msg, code=error_code),
                    "grant_refund_for_shipping": ValidationError(
                        error_msg, code=error_code
                    ),
                }
            )

    @classmethod
    def clean_input(
        cls,
        order: models.Order,
        input: dict[str, Any],
    ):
        amount = input.get("amount")
        reason = input.get("reason", "")
        input_lines = input.get("lines", [])
        grant_refund_for_shipping = input.get("grant_refund_for_shipping", None)

        cls.validate_input(input)

        cleaned_input_lines: list[models.OrderGrantedRefundLine] = []
        if input_lines:
            cleaned_input_lines, errors = cls.clean_input_lines(order, input_lines)
            if errors:
                raise ValidationError(
                    {
                        "lines": ValidationError(
                            "Provided input for lines is invalid.",
                            code=OrderGrantRefundCreateErrorCode.INVALID.value,
                            params={"lines": errors},
                        ),
                    }
                )
        if grant_refund_for_shipping and shipping_costs_already_granted(order):
            error_code = OrderGrantRefundCreateErrorCode.SHIPPING_COSTS_ALREADY_GRANTED
            raise ValidationError(
                {
                    "grant_refund_for_shipping": ValidationError(
                        "Shipping costs have already been granted.",
                        code=error_code.value,
                    )
                }
            )

        if amount is None:
            amount = cls.calculate_amount(
                order, cleaned_input_lines, grant_refund_for_shipping
            )

        return {
            "amount": amount,
            "reason": reason,
            "lines": cleaned_input_lines,
            "grant_refund_for_shipping": grant_refund_for_shipping,
        }

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        order = cls.get_node_or_error(info, id, only_type=Order)
        cleaned_input = cls.clean_input(order, input)
        amount = cleaned_input["amount"]
        reason = cleaned_input["reason"]
        cleaned_input_lines = cleaned_input["lines"]
        grant_refund_for_shipping = cleaned_input["grant_refund_for_shipping"]

        with transaction.atomic():
            granted_refund = order.granted_refunds.create(
                amount_value=amount,
                currency=order.currency,
                reason=reason,
                user=info.context.user,
                app=info.context.app,
                shipping_costs_included=grant_refund_for_shipping or False,
            )
            if cleaned_input_lines:
                for line in cleaned_input_lines:
                    line.granted_refund = granted_refund
                models.OrderGrantedRefundLine.objects.bulk_create(cleaned_input_lines)

        return cls(order=order, granted_refund=granted_refund)
