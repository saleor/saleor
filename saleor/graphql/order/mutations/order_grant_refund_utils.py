import uuid
from collections import defaultdict
from typing import Any, Optional, Union, cast

import graphene
from graphql import GraphQLError

from ....order import models
from ...core.utils import from_global_id_or_error


def shipping_costs_already_granted(order: models.Order):
    if order.granted_refunds.filter(shipping_costs_included=True):
        return True
    return False


def handle_lines_with_quantity_already_refunded(
    order: models.Order,
    input_lines_data: dict[uuid.UUID, models.OrderGrantedRefundLine],
    errors: list[dict[str, Any]],
    error_code: str,
    granted_refund_lines_to_exclude: Optional[list[int]] = None,
):
    all_granted_refund_ids = order.granted_refunds.all().values_list("id", flat=True)
    all_granted_refund_lines = models.OrderGrantedRefundLine.objects.filter(
        granted_refund_id__in=all_granted_refund_ids
    )
    if granted_refund_lines_to_exclude:
        all_granted_refund_lines.exclude(pk__in=granted_refund_lines_to_exclude)

    lines_with_quantity_already_refunded: dict[uuid.UUID, int] = defaultdict(int)
    for line in all_granted_refund_lines:
        lines_with_quantity_already_refunded[line.order_line_id] += line.quantity

    for granted_refund_line in input_lines_data.values():
        if not granted_refund_line.order_line:
            continue

        quantity_already_refunded = lines_with_quantity_already_refunded[
            granted_refund_line.order_line.pk
        ]

        if (
            granted_refund_line.quantity + quantity_already_refunded
            > granted_refund_line.order_line.quantity
        ):
            available_quantity = (
                granted_refund_line.order_line.quantity - quantity_already_refunded
            )
            errors.append(
                {
                    "line_id": graphene.Node.to_global_id(
                        "OrderLine", granted_refund_line.order_line.pk
                    ),
                    "field": "quantity",
                    "message": (
                        "Cannot grant refund for more than the available quantity "
                        f"of the line ({available_quantity})."
                    ),
                    "code": error_code,
                }
            )


def get_input_lines_data(
    lines: list[dict[str, Union[str, int]]],
    errors: list[dict[str, str]],
    error_code: str,
) -> dict[uuid.UUID, models.OrderGrantedRefundLine]:
    granted_refund_lines = {}
    for line in lines:
        order_line_id = cast(str, line["id"])
        try:
            _, pk = from_global_id_or_error(
                order_line_id, only_type="OrderLine", raise_error=True
            )
            uuid_pk = uuid.UUID(pk)
            reason = cast(Optional[str], line.get("reason"))
            granted_refund_lines[uuid_pk] = models.OrderGrantedRefundLine(
                order_line_id=uuid_pk,
                quantity=int(line["quantity"]),
                reason=reason,
            )
        except (GraphQLError, ValueError) as e:
            errors.append(
                {
                    "line_id": order_line_id,
                    "field": "id",
                    "code": error_code,
                    "message": str(e),
                }
            )
    return granted_refund_lines


def assign_order_lines(
    order: models.Order,
    input_lines_data: dict[uuid.UUID, models.OrderGrantedRefundLine],
    errors: list[dict[str, str]],
    error_code: str,
):
    input_line_ids = list(input_lines_data.keys())
    lines = order.lines.filter(id__in=input_line_ids)
    lines_dict = {line.pk: line for line in lines}
    if len(lines_dict.keys()) != len(input_line_ids):
        invalid_ids = set(input_line_ids).difference(set(lines_dict.keys()))
        for invalid_id in invalid_ids:
            errors.append(
                {
                    "line_id": graphene.Node.to_global_id("OrderLine", invalid_id),
                    "field": "id",
                    "message": "Could not resolve to a line.",
                    "code": error_code,
                }
            )
    for line_pk, order_line in lines_dict.items():
        input_lines_data[line_pk].order_line = order_line
