import uuid

import graphene
import pytest
from django.core.exceptions import ValidationError

from .....order import models
from .....page.models import Page, PageType
from ....core.utils import to_global_id_or_none
from ...enums import OrderGrantRefundCreateErrorCode
from ...mutations.order_grant_refund_utils import (
    resolve_per_line_reason_references,
    resolve_reason_reference_page,
)


@pytest.fixture
def refund_page_type(db):
    return PageType.objects.create(name="Refund Reasons", slug="refund-reasons")


@pytest.fixture
def refund_page(refund_page_type):
    return Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=refund_page_type,
        is_published=True,
    )


def test_resolves_valid_page(refund_page_type, refund_page):
    # Given
    page_id = to_global_id_or_none(refund_page)

    # When
    result = resolve_reason_reference_page(
        page_id, refund_page_type, OrderGrantRefundCreateErrorCode
    )

    # Then
    assert result == refund_page


def test_raises_graphql_error_for_wrong_type_id(refund_page_type):
    # Given
    invalid_id = graphene.Node.to_global_id("Product", 12345)

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        resolve_reason_reference_page(
            invalid_id, refund_page_type, OrderGrantRefundCreateErrorCode
        )
    error = exc_info.value.error_dict["reason_reference"][0]
    assert error.code == OrderGrantRefundCreateErrorCode.GRAPHQL_ERROR.value


def test_raises_invalid_for_wrong_page_type(refund_page_type):
    # Given
    other_type = PageType.objects.create(name="Other", slug="other")
    page = Page.objects.create(
        slug="other-page",
        title="Other Page",
        page_type=other_type,
        is_published=True,
    )
    page_id = to_global_id_or_none(page)

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        resolve_reason_reference_page(
            page_id, refund_page_type, OrderGrantRefundCreateErrorCode
        )
    error = exc_info.value.error_dict["reason_reference"][0]
    assert error.code == OrderGrantRefundCreateErrorCode.INVALID.value
    assert error.message == (
        "Invalid reason reference. Must be an ID of a Model (Page)"
    )


def test_raises_invalid_for_nonexistent_page(refund_page_type):
    # Given
    page_id = graphene.Node.to_global_id("Page", 99999)

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        resolve_reason_reference_page(
            page_id, refund_page_type, OrderGrantRefundCreateErrorCode
        )
    error = exc_info.value.error_dict["reason_reference"][0]
    assert error.code == OrderGrantRefundCreateErrorCode.INVALID.value


def test_resolves_reason_references_for_lines(
    refund_page_type, refund_page, order_with_lines
):
    # Given
    order_line = order_with_lines.lines.first()
    line = models.OrderGrantedRefundLine(
        order_line_id=order_line.pk,
        quantity=1,
        reason="Damaged",
    )
    page_id = to_global_id_or_none(refund_page)
    line_reason_ref_ids = {order_line.pk: page_id}

    # When
    resolve_per_line_reason_references(
        [line],
        line_reason_ref_ids,
        refund_page_type,
        OrderGrantRefundCreateErrorCode,
    )

    # Then
    assert line.reason_reference == refund_page


def test_skips_lines_without_reason_reference(refund_page_type, order_with_lines):
    # Given
    order_line = order_with_lines.lines.first()
    line = models.OrderGrantedRefundLine(
        order_line_id=order_line.pk,
        quantity=1,
        reason="Damaged",
    )
    line_reason_ref_ids: dict[uuid.UUID, str | None] = {order_line.pk: None}

    # When
    resolve_per_line_reason_references(
        [line],
        line_reason_ref_ids,
        refund_page_type,
        OrderGrantRefundCreateErrorCode,
    )

    # Then
    assert not hasattr(line, "_reason_reference_cache")


def test_raises_not_configured_when_type_missing(order_with_lines):
    # Given
    page_type = PageType.objects.create(name="Reasons", slug="reasons")
    page = Page.objects.create(
        slug="reason",
        title="Reason",
        page_type=page_type,
        is_published=True,
    )
    order_line = order_with_lines.lines.first()
    line = models.OrderGrantedRefundLine(
        order_line_id=order_line.pk,
        quantity=1,
        reason="Damaged",
    )
    page_id = to_global_id_or_none(page)
    line_reason_ref_ids = {order_line.pk: page_id}

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        resolve_per_line_reason_references(
            [line],
            line_reason_ref_ids,
            None,  # not configured
            OrderGrantRefundCreateErrorCode,
        )
    error = exc_info.value.error_dict["reason_reference"][0]
    assert error.code == OrderGrantRefundCreateErrorCode.NOT_CONFIGURED.value
    assert error.message == "Reason reference type is not configured."


def test_raises_invalid_for_wrong_page_type_in_line(refund_page_type, order_with_lines):
    # Given
    other_type = PageType.objects.create(name="Other", slug="other")
    page = Page.objects.create(
        slug="wrong-page",
        title="Wrong Page",
        page_type=other_type,
        is_published=True,
    )
    order_line = order_with_lines.lines.first()
    line = models.OrderGrantedRefundLine(
        order_line_id=order_line.pk,
        quantity=1,
        reason="Damaged",
    )
    page_id = to_global_id_or_none(page)
    line_reason_ref_ids = {order_line.pk: page_id}

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        resolve_per_line_reason_references(
            [line],
            line_reason_ref_ids,
            refund_page_type,
            OrderGrantRefundCreateErrorCode,
        )
    error = exc_info.value.error_dict["reason_reference"][0]
    assert error.code == OrderGrantRefundCreateErrorCode.INVALID.value
    assert error.message == (
        "Invalid reason reference. Must be an ID of a Model (Page)"
    )


def test_batches_db_queries(
    refund_page_type, order_with_lines, django_assert_num_queries
):
    # Given
    page1 = Page.objects.create(
        slug="reason-1",
        title="Reason 1",
        page_type=refund_page_type,
        is_published=True,
    )
    page2 = Page.objects.create(
        slug="reason-2",
        title="Reason 2",
        page_type=refund_page_type,
        is_published=True,
    )
    lines_qs = order_with_lines.lines.all()
    line1 = models.OrderGrantedRefundLine(
        order_line_id=lines_qs[0].pk,
        quantity=1,
    )
    line2 = models.OrderGrantedRefundLine(
        order_line_id=lines_qs[1].pk,
        quantity=1,
    )
    page1_id = to_global_id_or_none(page1)
    page2_id = to_global_id_or_none(page2)
    line_reason_ref_ids = {
        lines_qs[0].pk: page1_id,
        lines_qs[1].pk: page2_id,
    }

    # When / Then — only 1 DB query regardless of number of lines
    with django_assert_num_queries(1):
        resolve_per_line_reason_references(
            [line1, line2],
            line_reason_ref_ids,
            refund_page_type,
            OrderGrantRefundCreateErrorCode,
        )

    assert line1.reason_reference == page1
    assert line2.reason_reference == page2
