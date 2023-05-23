import decimal
import uuid
from collections import defaultdict
from typing import Any, Optional, Union, cast

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from graphql import GraphQLError

from ....order import models
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_313, ADDED_IN_314, PREVIEW_FEATURE
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.scalars import Decimal
from ...core.types import BaseInputObjectType
from ...core.types.common import Error, NonNullList
from ...core.utils import from_global_id_or_error
from ..enums import OrderGrantRefundCreateErrorCode, OrderGrantRefundCreateLineErrorCode
from ..types import Order, OrderGrantedRefund


class OrderGrantRefundCreateLineError(Error):
    code = OrderGrantRefundCreateLineErrorCode(
        description="The error code.", required=True
    )
    order_line_id = graphene.ID(
        description="The ID of the line related to the error.", required=True
    )


class OrderGrantRefundCreateError(Error):
    code = OrderGrantRefundCreateErrorCode(description="The error code.", required=True)
    lines = NonNullList(
        OrderGrantRefundCreateLineError,
        description="List of lines which cause the error.",
        required=False,
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderGrantRefundOrderLineInput(BaseInputObjectType):
    order_line_id = graphene.ID(description="The ID of the order line.", required=True)
    quantity = graphene.Int(
        description="The quantity of line items to be marked to refund.", required=True
    )

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
        OrderGrantRefundOrderLineInput,
        description="Lines to assing to granted refund."
        + ADDED_IN_314
        + PREVIEW_FEATURE,
        required=False,
    )
    grant_refund_for_shipping = graphene.Boolean(
        description="Determine if granted refund should include shipping costs."
        + ADDED_IN_314
        + PREVIEW_FEATURE
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
        cls, order: models.Order, lines: list[dict[str, Union[str, int]]]
    ) -> tuple[
        Optional[list[tuple[models.OrderLine, int]]], Optional[list[dict[str, str]]]
    ]:
        errors = []
        input_lines_data = {}
        for line in lines:
            order_line_id = cast(str, line["order_line_id"])
            try:
                _, pk = from_global_id_or_error(order_line_id, only_type="OrderLine")
                input_lines_data[pk] = int(line["quantity"])
            except GraphQLError as e:
                errors.append(
                    {
                        "order_line_id": line["order_line_id"],
                        "field": "orderLineId",
                        "code": OrderGrantRefundCreateLineErrorCode.GRAPHQL_ERROR.value,
                        "message": str(e),
                    }
                )

        input_line_ids = list(input_lines_data.keys())
        lines = order.lines.filter(id__in=input_line_ids)
        lines_dict = {line.pk: line for line in lines}
        if len(lines_dict.keys()) != len(input_line_ids):
            invalid_ids = set(input_line_ids).difference(set(lines_dict.keys()))
            for invalid_id in invalid_ids:
                errors.append(
                    {
                        "order_line_id": graphene.Node.to_global_id(
                            "OrderLine", invalid_id
                        ),
                        "field": "orderLineId",
                        "message": "Could not resolve to a line.",
                        "code": OrderGrantRefundCreateLineErrorCode.NOT_FOUND.value,
                    }
                )
        all_granted_refund_ids = order.granted_refunds.all().values_list(
            "id", flat=True
        )
        all_granted_refund_lines = models.OrderGrantedRefundLine.objects.filter(
            granted_refund_id__in=all_granted_refund_ids
        )
        lines_with_quantity_already_refunded: dict[uuid.UUID, int] = defaultdict(int)
        for line in all_granted_refund_lines:
            lines_with_quantity_already_refunded[line.order_line_id] += line.quantity

        for line in lines_dict.values():
            quantity_already_refunded = lines_with_quantity_already_refunded[line.pk]
            if (
                input_lines_data[str(line.pk)] + quantity_already_refunded
                > line.quantity
            ):
                error_code_class = OrderGrantRefundCreateLineErrorCode

                errors.append(
                    {
                        "order_line_id": graphene.Node.to_global_id(
                            "OrderLine", line.pk
                        ),
                        "field": "quantity",
                        "message": (
                            "Cannot grant refund for more than the available quantity "
                            f"of the line ({line.quantity-quantity_already_refunded})."
                        ),
                        "code": error_code_class.QUANTITY_GREATER_THAN_AVAILABLE.value,
                    }
                )

        if errors:
            return None, errors

        return [
            (line, input_lines_data[str(line.pk)]) for line in lines_dict.values()
        ], None

    @classmethod
    def shipping_costs_already_granted(cls, order: models.Order):
        if order.granted_refunds.filter(shipping_costs_included=True):
            return True
        return False

    @classmethod
    def calculate_amount(
        cls,
        order: models.Order,
        cleaned_input_lines: list[tuple[models.OrderLine, int]],
        grant_refund_for_shipping: bool,
    ) -> decimal.Decimal:
        amount = decimal.Decimal(0)
        for line, quantity in cleaned_input_lines:
            amount += line.unit_price_gross_amount * quantity
        if grant_refund_for_shipping:
            amount += order.shipping_price_gross_amount
        return amount

    @classmethod
    def clean_input(cls, order: models.Order, input: dict[str, Any]):
        amount = input.get("amount")
        reason = input.get("reason", "")
        input_lines = input.get("lines", [])
        grant_refund_for_shipping = input.get("grant_refund_for_shipping", False)

        if amount is None and not input_lines and not grant_refund_for_shipping:
            error_msg = (
                "You must provide at least one of `amount`, `lines`, "
                "`grantRefundForShipping`."
            )
            raise ValidationError(
                {
                    "amount": ValidationError(
                        error_msg,
                        code=OrderGrantRefundCreateErrorCode.REQUIRED.value,
                    ),
                    "lines": ValidationError(
                        error_msg,
                        code=OrderGrantRefundCreateErrorCode.REQUIRED.value,
                    ),
                    "grant_refund_for_shipping": ValidationError(
                        error_msg,
                        code=OrderGrantRefundCreateErrorCode.REQUIRED.value,
                    ),
                }
            )
        cleaned_input_lines: Optional[list[tuple[models.OrderLine, int]]] = []
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
        if grant_refund_for_shipping and cls.shipping_costs_already_granted(order):
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
            cleaned_input_lines = cast(
                list[tuple[models.OrderLine, int]], cleaned_input_lines
            )
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
                shipping_costs_included=grant_refund_for_shipping,
            )
            if cleaned_input_lines:
                models.OrderGrantedRefundLine.objects.bulk_create(
                    [
                        models.OrderGrantedRefundLine(
                            order_line=line,
                            quantity=quantity,
                            granted_refund=granted_refund,
                        )
                        for line, quantity in cleaned_input_lines
                    ]
                )
        return cls(order=order, granted_refund=granted_refund)
