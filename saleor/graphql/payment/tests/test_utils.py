import graphene
import pytest
from django.core.exceptions import ValidationError

from ....page.models import Page, PageType
from ....payment.error_codes import (
    TransactionRequestActionErrorCode,
    TransactionRequestRefundForGrantedRefundErrorCode,
)
from ..utils import (
    resolve_reason_reference_page,
    validate_and_resolve_refund_reason_context,
    validate_per_line_reason_reference,
)


def test_no_reference_type_configured_no_reference_id_provided(site_settings):
    # Given
    site_settings.refund_reason_reference_type = None
    site_settings.save()

    # When
    result = validate_and_resolve_refund_reason_context(
        reason_reference_id=None,
        requestor_is_user=True,
        refund_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
        site_settings=site_settings,
    )

    # Then
    assert result == {
        "is_passing_reason_reference_required": False,
        "refund_reason_reference_type": None,
        "should_apply": False,
    }


def test_no_reference_type_configured_reference_id_provided_raises_invalid(
    site_settings,
):
    # Given
    site_settings.refund_reason_reference_type = None
    site_settings.save()

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_and_resolve_refund_reason_context(
            reason_reference_id="some-id",
            requestor_is_user=True,
            refund_reference_field_name="refundReasonReference",
            error_code_enum=TransactionRequestActionErrorCode,
            site_settings=site_settings,
        )

    error_dict = exc_info.value.error_dict
    assert "refundReasonReference" in error_dict
    assert (
        error_dict["refundReasonReference"][0].code
        == TransactionRequestActionErrorCode.GRAPHQL_ERROR.value
    )
    assert "Reason reference type is not configured" in str(
        error_dict["refundReasonReference"][0]
    )


def test_reference_type_configured_no_reference_id_user_requestor_raises_required(
    site_settings,
):
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    page_type.save()
    site_settings.refund_reason_reference_type = page_type
    site_settings.save()

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_and_resolve_refund_reason_context(
            reason_reference_id=None,
            requestor_is_user=True,
            refund_reference_field_name="refundReasonReference",
            error_code_enum=TransactionRequestActionErrorCode,
            site_settings=site_settings,
        )

    error_dict = exc_info.value.error_dict
    assert "refundReasonReference" in error_dict
    assert (
        error_dict["refundReasonReference"][0].code
        == TransactionRequestActionErrorCode.REQUIRED.value
    )
    assert "Reason reference is required" in str(error_dict["refundReasonReference"][0])


def test_reference_type_configured_no_reference_id_app_requestor_success(
    site_settings,
):
    """Test when reference type is configured, no reference ID provided, but requestor is app - should succeed."""
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    page_type.save()
    site_settings.refund_reason_reference_type = page_type
    site_settings.save()

    # When
    result = validate_and_resolve_refund_reason_context(
        reason_reference_id=None,
        requestor_is_user=False,  # App requestor
        refund_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
        site_settings=site_settings,
    )

    # Then
    assert result == {
        "is_passing_reason_reference_required": True,
        "refund_reason_reference_type": page_type,
        "should_apply": False,
    }


def test_reference_type_configured_reference_id_provided_success(site_settings):
    """Test when reference type is configured and reference ID is provided - should succeed."""
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    page_type.save()
    site_settings.refund_reason_reference_type = page_type
    site_settings.save()

    # When
    result = validate_and_resolve_refund_reason_context(
        reason_reference_id="some-reference-id",
        requestor_is_user=True,
        refund_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
        site_settings=site_settings,
    )

    # Then
    assert result == {
        "is_passing_reason_reference_required": True,
        "refund_reason_reference_type": page_type,
        "should_apply": True,
    }


def test_reference_type_configured_reference_id_provided_app_requestor_success(
    site_settings,
):
    """Test when reference type is configured, reference ID is provided, and requestor is app - should succeed."""
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    page_type.save()
    site_settings.refund_reason_reference_type = page_type
    site_settings.save()

    # When
    result = validate_and_resolve_refund_reason_context(
        reason_reference_id="some-reference-id",
        requestor_is_user=False,  # App requestor
        refund_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
        site_settings=site_settings,
    )

    # Then
    assert result == {
        "is_passing_reason_reference_required": True,
        "refund_reason_reference_type": page_type,
        "should_apply": True,
    }


def test_custom_field_name_in_error_message(site_settings):
    # Given
    site_settings.refund_reason_reference_type = None
    site_settings.save()
    custom_field_name = "customReasonReference"

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_and_resolve_refund_reason_context(
            reason_reference_id="some-id",
            requestor_is_user=True,
            refund_reference_field_name=custom_field_name,
            error_code_enum=TransactionRequestActionErrorCode,
            site_settings=site_settings,
        )

    error_dict = exc_info.value.error_dict
    assert custom_field_name in error_dict
    assert (
        error_dict[custom_field_name][0].code
        == TransactionRequestActionErrorCode.GRAPHQL_ERROR.value
    )


def test_custom_field_name_in_required_error_message(site_settings):
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    page_type.save()
    site_settings.refund_reason_reference_type = page_type
    site_settings.save()
    custom_field_name = "customReasonReference"

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_and_resolve_refund_reason_context(
            reason_reference_id=None,
            requestor_is_user=True,
            refund_reference_field_name=custom_field_name,
            error_code_enum=TransactionRequestActionErrorCode,
            site_settings=site_settings,
        )

    error_dict = exc_info.value.error_dict
    assert custom_field_name in error_dict
    assert (
        error_dict[custom_field_name][0].code
        == TransactionRequestActionErrorCode.REQUIRED.value
    )


def test_different_error_code_enum(site_settings):
    """Test that the function works with different error code enums."""
    # Given
    site_settings.refund_reason_reference_type = None
    site_settings.save()

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_and_resolve_refund_reason_context(
            reason_reference_id="some-id",
            requestor_is_user=True,
            refund_reference_field_name="refundReasonReference",
            error_code_enum=TransactionRequestRefundForGrantedRefundErrorCode,
            site_settings=site_settings,
        )

    error_dict = exc_info.value.error_dict
    assert "refundReasonReference" in error_dict
    assert (
        error_dict["refundReasonReference"][0].code
        == TransactionRequestRefundForGrantedRefundErrorCode.GRAPHQL_ERROR.value
    )


def test_is_passing_reason_reference_required_when_no_reference_type(site_settings):
    # Given: No reference type configured
    site_settings.refund_reason_reference_type = None
    site_settings.save()

    # When
    result = validate_and_resolve_refund_reason_context(
        reason_reference_id=None,
        requestor_is_user=False,
        refund_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
        site_settings=site_settings,
    )

    # Then
    assert result["is_passing_reason_reference_required"] is False


def test_is_passing_reason_reference_required_when_reference_type_configured(
    site_settings,
):
    # Given: Reference type configured
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    page_type.save()
    site_settings.refund_reason_reference_type = page_type
    site_settings.save()

    # When
    result = validate_and_resolve_refund_reason_context(
        reason_reference_id=None,
        requestor_is_user=False,
        refund_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
        site_settings=site_settings,
    )

    # Then
    assert result["is_passing_reason_reference_required"] is True


# validate_per_line_reason_reference tests


def test_per_line_no_configured_type_no_id_success(site_settings):
    # given
    site_settings.refund_reason_reference_type = None
    site_settings.save()

    # when
    result = validate_per_line_reason_reference(
        reason_reference_id=None,
        site_settings=site_settings,
        error_code_enum=TransactionRequestActionErrorCode,
    )

    # then
    assert result["should_apply"] is False


def test_per_line_no_configured_type_id_provided_raises(site_settings):
    # given
    site_settings.refund_reason_reference_type = None
    site_settings.save()

    # when / then
    with pytest.raises(ValidationError) as exc_info:
        validate_per_line_reason_reference(
            reason_reference_id="some-id",
            site_settings=site_settings,
            error_code_enum=TransactionRequestActionErrorCode,
        )

    error_dict = exc_info.value.error_dict
    assert "reason_reference" in error_dict
    assert (
        error_dict["reason_reference"][0].code
        == TransactionRequestActionErrorCode.GRAPHQL_ERROR.value
    )


def test_per_line_configured_type_id_provided_should_apply(site_settings):
    # given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save()

    # when
    result = validate_per_line_reason_reference(
        reason_reference_id="some-id",
        site_settings=site_settings,
        error_code_enum=TransactionRequestActionErrorCode,
    )

    # then
    assert result["should_apply"] is True
    assert result["refund_reason_reference_type"] == page_type


def test_per_line_configured_type_no_id_should_not_apply(site_settings):
    # given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    site_settings.refund_reason_reference_type = page_type
    site_settings.save()

    # when
    result = validate_per_line_reason_reference(
        reason_reference_id=None,
        site_settings=site_settings,
        error_code_enum=TransactionRequestActionErrorCode,
    )

    # then
    assert result["should_apply"] is False


# resolve_reason_reference_page tests


def test_resolve_reason_reference_page_valid(site_settings):
    # given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    page = Page.objects.create(
        slug="damaged-product",
        title="Damaged Product",
        page_type=page_type,
        is_published=True,
    )
    page_global_id = graphene.Node.to_global_id("Page", page.pk)

    # when
    result = resolve_reason_reference_page(
        page_global_id,
        page_type.pk,
        TransactionRequestActionErrorCode,
    )

    # then
    assert result == page


def test_resolve_reason_reference_page_wrong_page_type(site_settings):
    # given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    wrong_page_type = PageType.objects.create(name="Blog Posts", slug="blog-posts")
    page = Page.objects.create(
        slug="blog-post",
        title="Blog Post",
        page_type=wrong_page_type,
        is_published=True,
    )
    page_global_id = graphene.Node.to_global_id("Page", page.pk)

    # when / then
    with pytest.raises(ValidationError) as exc_info:
        resolve_reason_reference_page(
            page_global_id,
            page_type.pk,
            TransactionRequestActionErrorCode,
        )

    error_dict = exc_info.value.error_dict
    assert "reason_reference" in error_dict
    assert (
        error_dict["reason_reference"][0].code
        == TransactionRequestActionErrorCode.GRAPHQL_ERROR.value
    )


def test_resolve_reason_reference_page_invalid_global_id(site_settings):
    # given
    page_type = PageType.objects.create(name="Refund Reasons", slug="refund-reasons")
    product_global_id = graphene.Node.to_global_id("Product", 1)

    # when / then
    with pytest.raises(ValidationError) as exc_info:
        resolve_reason_reference_page(
            product_global_id,
            page_type.pk,
            TransactionRequestActionErrorCode,
        )

    error_dict = exc_info.value.error_dict
    assert "reason_reference" in error_dict
    assert (
        error_dict["reason_reference"][0].code
        == TransactionRequestActionErrorCode.GRAPHQL_ERROR.value
    )
