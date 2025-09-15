from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from ....page.models import PageType
from ....payment.error_codes import (
    TransactionRequestActionErrorCode,
    TransactionRequestRefundForGrantedRefundErrorCode,
)
from ....site.models import SiteSettings
from ..utils import validate_and_resolve_refund_reason_context


@patch("saleor.graphql.payment.utils.Site.objects.get_current")
def test_no_reference_type_configured_no_reference_id_provided(mock_get_current):
    # Given
    mock_settings = SiteSettings()
    mock_settings.refund_reason_reference_type = None
    mock_site = type("Site", (), {"settings": mock_settings})()
    mock_get_current.return_value = mock_site

    # When
    result = validate_and_resolve_refund_reason_context(
        reason_reference_id=None,
        requestor_is_user=True,
        refund_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
    )

    # Then
    assert result == {
        "is_passing_reason_reference_required": False,
        "refund_reason_reference_type": None,
        "should_apply": False,
    }


@patch("saleor.graphql.payment.utils.Site.objects.get_current")
def test_no_reference_type_configured_reference_id_provided_raises_invalid(
    mock_get_current,
):
    # Given
    mock_settings = SiteSettings()
    mock_settings.refund_reason_reference_type = None
    mock_site = type("Site", (), {"settings": mock_settings})()
    mock_get_current.return_value = mock_site

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_and_resolve_refund_reason_context(
            reason_reference_id="some-id",
            requestor_is_user=True,
            refund_reference_field_name="refundReasonReference",
            error_code_enum=TransactionRequestActionErrorCode,
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


@patch("saleor.graphql.payment.utils.Site.objects.get_current")
def test_reference_type_configured_no_reference_id_user_requestor_raises_required(
    mock_get_current,
):
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    mock_settings = SiteSettings()
    mock_settings.refund_reason_reference_type = page_type
    mock_site = type("Site", (), {"settings": mock_settings})()
    mock_get_current.return_value = mock_site

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_and_resolve_refund_reason_context(
            reason_reference_id=None,
            requestor_is_user=True,
            refund_reference_field_name="refundReasonReference",
            error_code_enum=TransactionRequestActionErrorCode,
        )

    error_dict = exc_info.value.error_dict
    assert "refundReasonReference" in error_dict
    assert (
        error_dict["refundReasonReference"][0].code
        == TransactionRequestActionErrorCode.REQUIRED.value
    )
    assert "Reason reference is required" in str(error_dict["refundReasonReference"][0])


@patch("saleor.graphql.payment.utils.Site.objects.get_current")
def test_reference_type_configured_no_reference_id_app_requestor_success(
    mock_get_current,
):
    """Test when reference type is configured, no reference ID provided, but requestor is app - should succeed."""
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    mock_settings = SiteSettings()
    mock_settings.refund_reason_reference_type = page_type
    mock_site = type("Site", (), {"settings": mock_settings})()
    mock_get_current.return_value = mock_site

    # When
    result = validate_and_resolve_refund_reason_context(
        reason_reference_id=None,
        requestor_is_user=False,  # App requestor
        refund_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
    )

    # Then
    assert result == {
        "is_passing_reason_reference_required": True,
        "refund_reason_reference_type": page_type,
        "should_apply": False,
    }


@patch("saleor.graphql.payment.utils.Site.objects.get_current")
def test_reference_type_configured_reference_id_provided_success(mock_get_current):
    """Test when reference type is configured and reference ID is provided - should succeed."""
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    mock_settings = SiteSettings()
    mock_settings.refund_reason_reference_type = page_type
    mock_site = type("Site", (), {"settings": mock_settings})()
    mock_get_current.return_value = mock_site

    # When
    result = validate_and_resolve_refund_reason_context(
        reason_reference_id="some-reference-id",
        requestor_is_user=True,
        refund_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
    )

    # Then
    assert result == {
        "is_passing_reason_reference_required": True,
        "refund_reason_reference_type": page_type,
        "should_apply": True,
    }


@patch("saleor.graphql.payment.utils.Site.objects.get_current")
def test_reference_type_configured_reference_id_provided_app_requestor_success(
    mock_get_current,
):
    """Test when reference type is configured, reference ID is provided, and requestor is app - should succeed."""
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    mock_settings = SiteSettings()
    mock_settings.refund_reason_reference_type = page_type
    mock_site = type("Site", (), {"settings": mock_settings})()
    mock_get_current.return_value = mock_site

    # When
    result = validate_and_resolve_refund_reason_context(
        reason_reference_id="some-reference-id",
        requestor_is_user=False,  # App requestor
        refund_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
    )

    # Then
    assert result == {
        "is_passing_reason_reference_required": True,
        "refund_reason_reference_type": page_type,
        "should_apply": True,
    }


@patch("saleor.graphql.payment.utils.Site.objects.get_current")
def test_custom_field_name_in_error_message(mock_get_current):
    # Given
    mock_settings = SiteSettings()
    mock_settings.refund_reason_reference_type = None
    mock_site = type("Site", (), {"settings": mock_settings})()
    mock_get_current.return_value = mock_site
    custom_field_name = "customReasonReference"

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_and_resolve_refund_reason_context(
            reason_reference_id="some-id",
            requestor_is_user=True,
            refund_reference_field_name=custom_field_name,
            error_code_enum=TransactionRequestActionErrorCode,
        )

    error_dict = exc_info.value.error_dict
    assert custom_field_name in error_dict
    assert (
        error_dict[custom_field_name][0].code
        == TransactionRequestActionErrorCode.INVALID.value
    )


@patch("saleor.graphql.payment.utils.Site.objects.get_current")
def test_custom_field_name_in_required_error_message(mock_get_current):
    # Given
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")
    mock_settings = SiteSettings()
    mock_settings.refund_reason_reference_type = page_type
    mock_site = type("Site", (), {"settings": mock_settings})()
    mock_get_current.return_value = mock_site
    custom_field_name = "customReasonReference"

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_and_resolve_refund_reason_context(
            reason_reference_id=None,
            requestor_is_user=True,
            refund_reference_field_name=custom_field_name,
            error_code_enum=TransactionRequestActionErrorCode,
        )

    error_dict = exc_info.value.error_dict
    assert custom_field_name in error_dict
    assert (
        error_dict[custom_field_name][0].code
        == TransactionRequestActionErrorCode.REQUIRED.value
    )


@patch("saleor.graphql.payment.utils.Site.objects.get_current")
def test_different_error_code_enum(mock_get_current):
    """Test that the function works with different error code enums."""
    # Given
    mock_settings = SiteSettings()
    mock_settings.refund_reason_reference_type = None
    mock_site = type("Site", (), {"settings": mock_settings})()
    mock_get_current.return_value = mock_site

    # When / Then
    with pytest.raises(ValidationError) as exc_info:
        validate_and_resolve_refund_reason_context(
            reason_reference_id="some-id",
            requestor_is_user=True,
            refund_reference_field_name="refundReasonReference",
            error_code_enum=TransactionRequestRefundForGrantedRefundErrorCode,
        )

    error_dict = exc_info.value.error_dict
    assert "refundReasonReference" in error_dict
    assert (
        error_dict["refundReasonReference"][0].code
        == TransactionRequestRefundForGrantedRefundErrorCode.INVALID.value
    )


@patch("saleor.graphql.payment.utils.Site.objects.get_current")
def test_is_passing_reason_reference_required_logic(mock_get_current):
    page_type = PageType(name="Refund Reasons", slug="refund-reasons")

    # Case 1: No reference type configured
    mock_settings = SiteSettings()
    mock_settings.refund_reason_reference_type = None
    mock_site = type("Site", (), {"settings": mock_settings})()
    mock_get_current.return_value = mock_site

    result = validate_and_resolve_refund_reason_context(
        reason_reference_id=None,
        requestor_is_user=False,
        refund_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
    )

    assert result["is_passing_reason_reference_required"] is False

    # Case 2: Reference type configured
    mock_settings.refund_reason_reference_type = page_type

    result = validate_and_resolve_refund_reason_context(
        reason_reference_id=None,
        requestor_is_user=False,
        refund_reference_field_name="refundReasonReference",
        error_code_enum=TransactionRequestActionErrorCode,
    )

    assert result["is_passing_reason_reference_required"] is True
