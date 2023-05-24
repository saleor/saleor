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
    lines_dict: dict[uuid.UUID, models.OrderLine],
    input_lines_data: dict[str, int],
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

    for line in lines_dict.values():
        quantity_already_refunded = lines_with_quantity_already_refunded[line.pk]
        if input_lines_data[str(line.pk)] + quantity_already_refunded > line.quantity:
            errors.append(
                {
                    "line_id": graphene.Node.to_global_id("OrderLine", line.pk),
                    "field": "quantity",
                    "message": (
                        "Cannot grant refund for more than the available quantity "
                        f"of the line ({line.quantity - quantity_already_refunded})."
                    ),
                    "code": error_code,
                }
            )


def get_input_lines_data(
    lines: list[dict[str, Union[str, int]]],
    errors: list[dict[str, str]],
    error_code: str,
) -> dict[str, int]:
    input_lines_data = {}
    for line in lines:
        order_line_id = cast(str, line["id"])
        try:
            _, pk = from_global_id_or_error(
                order_line_id, only_type="OrderLine", raise_error=True
            )
            input_lines_data[pk] = int(line["quantity"])
        except GraphQLError as e:
            errors.append(
                {
                    "line_id": order_line_id,
                    "field": "id",
                    "code": error_code,
                    "message": str(e),
                }
            )
    return input_lines_data


def get_lines_map(
    order: models.Order,
    input_lines_data: dict[str, int],
    errors: list[dict[str, str]],
    error_code: str,
) -> dict[uuid.UUID, models.OrderLine]:
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
    return lines_dict
