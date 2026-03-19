import uuid
from collections import defaultdict
from typing import Any, TypedDict

import graphene
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from ....order import models
from ....page.models import Page
from ...core.utils import from_global_id_or_error


class GrantRefundLineDict(TypedDict, total=False):
    id: str
    quantity: int
    reason: str
    reason_reference: str


def shipping_costs_already_granted(
    order: models.Order, grant_refund_pk_to_exclude=None
):
    qs = order.granted_refunds.filter(shipping_costs_included=True)
    if grant_refund_pk_to_exclude:
        qs = qs.exclude(pk=grant_refund_pk_to_exclude)
    if qs.exists():
        return True
    return False


def handle_lines_with_quantity_already_refunded(
    order: models.Order,
    input_lines_data: dict[uuid.UUID, models.OrderGrantedRefundLine],
    errors: list[dict[str, Any]],
    error_code: str,
    granted_refund_lines_to_exclude: list[int] | None = None,
):
    all_granted_refund_ids = order.granted_refunds.all().values_list("id", flat=True)
    all_granted_refund_lines = models.OrderGrantedRefundLine.objects.filter(
        granted_refund_id__in=all_granted_refund_ids
    )
    lines_to_process = all_granted_refund_lines
    if granted_refund_lines_to_exclude:
        lines_to_process = all_granted_refund_lines.exclude(
            pk__in=granted_refund_lines_to_exclude
        )

    lines_with_quantity_already_refunded: dict[uuid.UUID, int] = defaultdict(int)
    for line in lines_to_process:
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


def validate_reason_references(
    lines: list[GrantRefundLineDict],
    refund_reason_reference_type_pk: int | None,
    errors: list[dict[str, Any]],
    line_error_code_enum: Any,
) -> dict[str, int]:
    """Validate reason_reference IDs upfront and return a {global_id: page_pk} map."""
    refs_by_line: list[tuple[str, str]] = []
    for line in lines:
        reason_ref = line.get("reason_reference")
        if reason_ref:
            refs_by_line.append((line["id"], reason_ref))

    if not refs_by_line:
        return {}

    if not refund_reason_reference_type_pk:
        for order_line_id, _ in refs_by_line:
            errors.append(
                {
                    "line_id": order_line_id,
                    "field": "reason_reference",
                    "message": "Reason reference type is not configured.",
                    "code": line_error_code_enum.NOT_CONFIGURED.value,
                }
            )
        return {}

    # Parse all global IDs to PKs
    page_pks: dict[str, int] = {}  # reason_reference global_id -> pk
    for order_line_id, global_id in refs_by_line:
        try:
            _, pk_str = from_global_id_or_error(
                global_id, only_type="Page", raise_error=True
            )
        except (GraphQLError, ValueError) as e:
            errors.append(
                {
                    "line_id": order_line_id,
                    "field": "reason_reference",
                    "message": str(e),
                    "code": line_error_code_enum.GRAPHQL_ERROR.value,
                }
            )
            continue
        page_pks[global_id] = int(pk_str)

    if errors:
        return {}

    existing_page_pks: set[int] = set(
        Page.objects.filter(
            pk__in=page_pks.values(),
            page_type=refund_reason_reference_type_pk,
        ).values_list("pk", flat=True)
    )

    reason_reference_map: dict[str, int] = {}
    for order_line_id, global_id in refs_by_line:
        page_pk = page_pks[global_id]
        if page_pk not in existing_page_pks:
            errors.append(
                {
                    "line_id": order_line_id,
                    "field": "reason_reference",
                    "message": "Invalid reason reference.",
                    "code": line_error_code_enum.INVALID.value,
                }
            )
        else:
            reason_reference_map[global_id] = page_pk

    return reason_reference_map


def get_input_lines_data(
    lines: list[GrantRefundLineDict],
    errors: list[dict[str, str]],
    error_code: str,
    reason_reference_map: dict[str, int],
) -> dict[uuid.UUID, models.OrderGrantedRefundLine]:
    input_lines: dict[uuid.UUID, models.OrderGrantedRefundLine] = {}
    for line in lines:
        order_line_id = line["id"]
        try:
            _, pk = from_global_id_or_error(
                order_line_id, only_type="OrderLine", raise_error=True
            )
            uuid_pk = uuid.UUID(pk)
            reason = line.get("reason")
            reason_ref_gid = line.get("reason_reference")
            reason_reference_id = (
                reason_reference_map.get(reason_ref_gid) if reason_ref_gid else None
            )
            input_lines[uuid_pk] = models.OrderGrantedRefundLine(
                order_line_id=uuid_pk,
                quantity=line["quantity"],
                reason=reason,
                reason_reference_id=reason_reference_id,
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
    return input_lines


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


def resolve_reason_reference_page(
    reason_reference_id: str,
    reason_reference_type_pk: int,
    error_code_enum: Any,
) -> Page:
    """Resolve a reason_reference global ID to a Page instance.

    Validates the Page belongs to the expected PageType.
    """
    try:
        _, pk = from_global_id_or_error(
            reason_reference_id, only_type="Page", raise_error=True
        )
    except GraphQLError as e:
        raise ValidationError(
            {
                "reason_reference": ValidationError(
                    str(e),
                    code=error_code_enum.GRAPHQL_ERROR.value,
                )
            }
        ) from None

    try:
        return Page.objects.get(pk=pk, page_type=reason_reference_type_pk)
    except (Page.DoesNotExist, ValueError):
        raise ValidationError(
            {
                "reason_reference": ValidationError(
                    "Invalid reason reference. Must be an ID of a Model (Page)",
                    code=error_code_enum.INVALID.value,
                )
            }
        ) from None


def clean_grant_refund_lines(
    *,
    order: models.Order,
    lines: list[GrantRefundLineDict],
    refund_reason_reference_type_pk: int | None,
    errors: list[dict[str, Any]],
    line_error_code_enum: Any,
    granted_refund_lines_to_exclude: list[int] | None = None,
) -> list[models.OrderGrantedRefundLine]:
    reason_reference_map = validate_reason_references(
        lines, refund_reason_reference_type_pk, errors, line_error_code_enum
    )
    input_lines_data = get_input_lines_data(
        lines, errors, line_error_code_enum.GRAPHQL_ERROR.value, reason_reference_map
    )
    assign_order_lines(
        order,
        input_lines_data,
        errors,
        line_error_code_enum.NOT_FOUND.value,
    )
    handle_lines_with_quantity_already_refunded(
        order,
        input_lines_data,
        errors,
        line_error_code_enum.QUANTITY_GREATER_THAN_AVAILABLE.value,
        granted_refund_lines_to_exclude=granted_refund_lines_to_exclude,
    )
    return list(input_lines_data.values())
