import pytest
from django.core.exceptions import ValidationError

from ....page.models import PageType
from ....payment.error_codes import (
    TransactionRequestActionErrorCode,
    TransactionRequestRefundForGrantedRefundErrorCode,
)
from ..utils import validate_reason_reference_context


def test_no_reference_type_configured_no_reference_id_provided():
    # Given / When
    should_apply = validate_reason_reference_context(
        reason_reference_id=None,
        requestor_is_user=True,
        reason_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
        reason_reference_type=None,
    )

    # Then
    assert should_apply is False


def test_no_reference_type_configured_reference_id_provided_raises_invalid():
    # Given / When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_reason_reference_context(
            reason_reference_id="some-id",
            requestor_is_user=True,
            reason_reference_field_name="refundReasonReference",
            error_code_enum=TransactionRequestActionErrorCode,
            reason_reference_type=None,
        )

    error_dict = exc_info.value.error_dict
    assert "refundReasonReference" in error_dict
    assert (
        error_dict["refundReasonReference"][0].code
        == TransactionRequestActionErrorCode.INVALID.value
    )
    assert "Reason reference type is not configured" in str(
        error_dict["refundReasonReference"][0]
    )


def test_reference_type_configured_no_reference_id_user_requestor_raises_required():
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    page_type.save()

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_reason_reference_context(
            reason_reference_id=None,
            requestor_is_user=True,
            reason_reference_field_name="refundReasonReference",
            error_code_enum=TransactionRequestActionErrorCode,
            reason_reference_type=page_type,
        )

    error_dict = exc_info.value.error_dict
    assert "refundReasonReference" in error_dict
    assert (
        error_dict["refundReasonReference"][0].code
        == TransactionRequestActionErrorCode.REQUIRED.value
    )
    assert "Reason reference is required" in str(error_dict["refundReasonReference"][0])


def test_reference_type_configured_no_reference_id_app_requestor_success():
    """Test when reference type is configured, no reference ID provided, but requestor is app - should succeed."""
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    page_type.save()

    # When
    should_apply = validate_reason_reference_context(
        reason_reference_id=None,
        requestor_is_user=False,  # App requestor
        reason_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
        reason_reference_type=page_type,
    )

    # Then
    assert should_apply is False


def test_reference_type_configured_reference_id_provided_success():
    """Test when reference type is configured and reference ID is provided - should succeed."""
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    page_type.save()

    # When
    should_apply = validate_reason_reference_context(
        reason_reference_id="some-reference-id",
        requestor_is_user=True,
        reason_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
        reason_reference_type=page_type,
    )

    # Then
    assert should_apply is True


def test_reference_type_configured_reference_id_provided_app_requestor_success():
    """Test when reference type is configured, reference ID is provided, and requestor is app - should succeed."""
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    page_type.save()

    # When
    should_apply = validate_reason_reference_context(
        reason_reference_id="some-reference-id",
        requestor_is_user=False,  # App requestor
        reason_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
        reason_reference_type=page_type,
    )

    # Then
    assert should_apply is True


def test_custom_field_name_in_error_message():
    # Given
    custom_field_name = "customReasonReference"

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_reason_reference_context(
            reason_reference_id="some-id",
            requestor_is_user=True,
            reason_reference_field_name=custom_field_name,
            error_code_enum=TransactionRequestActionErrorCode,
            reason_reference_type=None,
        )

    error_dict = exc_info.value.error_dict
    assert custom_field_name in error_dict
    assert (
        error_dict[custom_field_name][0].code
        == TransactionRequestActionErrorCode.INVALID.value
    )


def test_custom_field_name_in_required_error_message():
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    page_type.save()
    custom_field_name = "customReasonReference"

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_reason_reference_context(
            reason_reference_id=None,
            requestor_is_user=True,
            reason_reference_field_name=custom_field_name,
            error_code_enum=TransactionRequestActionErrorCode,
            reason_reference_type=page_type,
        )

    error_dict = exc_info.value.error_dict
    assert custom_field_name in error_dict
    assert (
        error_dict[custom_field_name][0].code
        == TransactionRequestActionErrorCode.REQUIRED.value
    )


def test_different_error_code_enum():
    """Test that the function works with different error code enums."""
    # Given / When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_reason_reference_context(
            reason_reference_id="some-id",
            requestor_is_user=True,
            reason_reference_field_name="refundReasonReference",
            error_code_enum=TransactionRequestRefundForGrantedRefundErrorCode,
            reason_reference_type=None,
        )

    error_dict = exc_info.value.error_dict
    assert "refundReasonReference" in error_dict
    assert (
        error_dict["refundReasonReference"][0].code
        == TransactionRequestRefundForGrantedRefundErrorCode.INVALID.value
    )
