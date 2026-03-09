import uuid
from collections import defaultdict
from typing import Any, cast

import graphene
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from ....order import models
from ....page.models import Page, PageType
from ...core.utils import from_global_id_or_error


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


def get_input_lines_data(
    lines: list[dict[str, str | int]],
    errors: list[dict[str, str]],
    error_code: str,
) -> tuple[dict[uuid.UUID, models.OrderGrantedRefundLine], dict[uuid.UUID, str | None]]:
    granted_refund_lines = {}
    line_reason_reference_ids: dict[uuid.UUID, str | None] = {}
    for line in lines:
        order_line_id = cast(str, line["id"])
        try:
            _, pk = from_global_id_or_error(
                order_line_id, only_type="OrderLine", raise_error=True
            )
            uuid_pk = uuid.UUID(pk)
            reason = cast(str | None, line.get("reason"))
            reason_reference_id = cast(str | None, line.get("reason_reference"))
            granted_refund_lines[uuid_pk] = models.OrderGrantedRefundLine(
                order_line_id=uuid_pk,
                quantity=int(line["quantity"]),
                reason=reason,
            )
            line_reason_reference_ids[uuid_pk] = reason_reference_id
        except (GraphQLError, ValueError) as e:
            errors.append(
                {
                    "line_id": order_line_id,
                    "field": "id",
                    "code": error_code,
                    "message": str(e),
                }
            )
    return granted_refund_lines, line_reason_reference_ids


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
    reason_reference_type: PageType,
    error_code_enum,
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
        return Page.objects.get(pk=pk, page_type=reason_reference_type.pk)
    except (Page.DoesNotExist, ValueError):
        raise ValidationError(
            {
                "reason_reference": ValidationError(
                    "Invalid reason reference. Must be an ID of a Model (Page)",
                    code=error_code_enum.INVALID.value,
                )
            }
        ) from None


def resolve_per_line_reason_references(
    lines: list[models.OrderGrantedRefundLine],
    line_reason_reference_ids: dict[uuid.UUID, str | None],
    refund_reason_reference_type: PageType | None,
    error_code_enum,
) -> None:
    """Resolve per-line reason_reference IDs and set on line instances.

    Batches DB lookups: collects all page IDs, fetches in one query, maps back.
    """
    has_any_reason_ref = any(
        line_reason_reference_ids.get(line.order_line_id) for line in lines
    )
    if not has_any_reason_ref:
        return

    if not refund_reason_reference_type:
        raise ValidationError(
            {
                "reason_reference": ValidationError(
                    "Reason reference type is not configured.",
                    code=error_code_enum.NOT_CONFIGURED.value,
                )
            }
        )

    # Collect all non-null reason_reference global IDs from lines
    lines_with_refs: list[tuple[models.OrderGrantedRefundLine, str]] = []
    for line in lines:
        reason_ref_id = line_reason_reference_ids.get(line.order_line_id)
        if reason_ref_id:
            lines_with_refs.append((line, reason_ref_id))

    # Parse all global IDs to PKs
    page_pks: dict[str, int] = {}  # global_id -> pk
    for _, global_id in lines_with_refs:
        try:
            _, pk_str = from_global_id_or_error(
                global_id, only_type="Page", raise_error=True
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
        page_pks[global_id] = int(pk_str)

    # Single DB query for all pages
    pages_by_pk: dict[int, Page] = {
        page.pk: page
        for page in Page.objects.filter(
            pk__in=page_pks.values(),
            page_type=refund_reason_reference_type.pk,
        )
    }

    # Map back to lines
    for line, global_id in lines_with_refs:
        page = pages_by_pk.get(page_pks[global_id])
        if not page:
            raise ValidationError(
                {
                    "reason_reference": ValidationError(
                        "Invalid reason reference. Must be an ID of a Model (Page)",
                        code=error_code_enum.INVALID.value,
                    )
                }
            )
        line.reason_reference = page
