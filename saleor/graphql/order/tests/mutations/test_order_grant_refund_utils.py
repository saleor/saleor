import graphene
import pytest
from django.core.exceptions import ValidationError

from .....order.error_codes import OrderGrantRefundCreateLineErrorCode
from .....page.models import Page, PageType
from ....core.utils import to_global_id_or_none
from ...enums import OrderGrantRefundCreateErrorCode
from ...mutations.order_grant_refund_utils import (
    resolve_reason_reference_page,
    validate_reason_references,
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
    assert error.message == (
        "Invalid reason reference. Must be an ID of a Model (Page)"
    )


def test_validate_reason_references_resolves_valid_page(
    refund_page_type, refund_page, order_with_lines
):
    # Given
    order_line = order_with_lines.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)
    page_id = to_global_id_or_none(refund_page)
    lines = [
        {
            "id": order_line_id,
            "quantity": 1,
            "reason": "Damaged",
            "reason_reference": page_id,
        }
    ]
    errors: list = []

    # When
    result = validate_reason_references(
        lines=lines,
        refund_reason_reference_type_pk=refund_page_type.pk,
        errors=errors,
        line_error_code_enum=OrderGrantRefundCreateLineErrorCode,
    )

    # Then
    assert not errors
    assert result == {page_id: refund_page.pk}


def test_validate_reason_references_skips_lines_without_reference(
    refund_page_type, order_with_lines
):
    # Given
    order_line = order_with_lines.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)
    lines = [{"id": order_line_id, "quantity": 1, "reason": "Damaged"}]
    errors: list = []

    # When
    result = validate_reason_references(
        lines=lines,
        refund_reason_reference_type_pk=refund_page_type.pk,
        errors=errors,
        line_error_code_enum=OrderGrantRefundCreateLineErrorCode,
    )

    # Then
    assert not errors
    assert result == {}


def test_validate_reason_references_reports_not_configured_per_line(
    page, order_with_lines
):
    # Given
    order_line = order_with_lines.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)
    page_id = to_global_id_or_none(page)
    lines = [
        {
            "id": order_line_id,
            "quantity": 1,
            "reason": "Damaged",
            "reason_reference": page_id,
        }
    ]
    errors: list = []

    # When
    validate_reason_references(
        lines=lines,
        refund_reason_reference_type_pk=None,
        errors=errors,
        line_error_code_enum=OrderGrantRefundCreateLineErrorCode,
    )

    # Then
    assert len(errors) == 1
    line_error = errors[0]
    assert (
        line_error["code"] == OrderGrantRefundCreateLineErrorCode.NOT_CONFIGURED.value
    )
    assert line_error["message"] == "Reason reference type is not configured."
    assert line_error["line_id"] == order_line_id


def test_validate_reason_references_reports_invalid_per_line(
    refund_page_type, order_with_lines
):
    # Given
    other_type = PageType.objects.create(name="Other", slug="other")
    page = Page.objects.create(
        slug="wrong-page",
        title="Wrong Page",
        page_type=other_type,
        is_published=True,
    )
    order_line = order_with_lines.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)
    page_id = to_global_id_or_none(page)
    lines = [
        {
            "id": order_line_id,
            "quantity": 1,
            "reason": "Damaged",
            "reason_reference": page_id,
        }
    ]
    errors: list = []

    # When
    validate_reason_references(
        lines=lines,
        refund_reason_reference_type_pk=refund_page_type.pk,
        errors=errors,
        line_error_code_enum=OrderGrantRefundCreateLineErrorCode,
    )

    # Then
    assert len(errors) == 1
    line_error = errors[0]
    assert line_error["code"] == OrderGrantRefundCreateLineErrorCode.INVALID.value
    assert line_error["message"] == "Invalid reason reference."
    assert line_error["line_id"] == order_line_id


def test_validate_reason_references_reports_graphql_error_per_line(
    refund_page_type, order_with_lines
):
    # Given
    order_line = order_with_lines.lines.first()
    order_line_id = graphene.Node.to_global_id("OrderLine", order_line.pk)
    invalid_id = graphene.Node.to_global_id("Product", 12345)
    lines = [
        {
            "id": order_line_id,
            "quantity": 1,
            "reason": "Damaged",
            "reason_reference": invalid_id,
        }
    ]
    errors: list = []

    # When
    validate_reason_references(
        lines=lines,
        refund_reason_reference_type_pk=refund_page_type.pk,
        errors=errors,
        line_error_code_enum=OrderGrantRefundCreateLineErrorCode,
    )

    # Then
    assert len(errors) == 1
    line_error = errors[0]
    assert line_error["code"] == OrderGrantRefundCreateLineErrorCode.GRAPHQL_ERROR.value
    assert line_error["message"] == (
        f"Invalid ID: {invalid_id}. Expected: Page, received: Product."
    )
    assert line_error["line_id"] == order_line_id


def test_validate_reason_references_batches_db_queries(
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
    line1_id = graphene.Node.to_global_id("OrderLine", lines_qs[0].pk)
    line2_id = graphene.Node.to_global_id("OrderLine", lines_qs[1].pk)
    page1_id = to_global_id_or_none(page1)
    page2_id = to_global_id_or_none(page2)
    lines = [
        {"id": line1_id, "quantity": 1, "reason_reference": page1_id},
        {"id": line2_id, "quantity": 1, "reason_reference": page2_id},
    ]
    errors: list = []

    # When / Then — only 1 DB query regardless of number of lines
    with django_assert_num_queries(1):
        result = validate_reason_references(
            lines=lines,
            refund_reason_reference_type_pk=refund_page_type.pk,
            errors=errors,
            line_error_code_enum=OrderGrantRefundCreateLineErrorCode,
        )

    assert not errors
    assert result == {page1_id: page1.pk, page2_id: page2.pk}
