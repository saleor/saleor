import pytest
from django.core.exceptions import ValidationError

from ....page.models import PageType
from ....payment.error_codes import TransactionRequestActionErrorCode
from ..utils import validate_per_line_reason_reference


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
        == TransactionRequestActionErrorCode.INVALID.value
    )
    assert "Reason reference type is not configured" in str(
        error_dict["reason_reference"][0]
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
    assert result["reason_reference_type"] == page_type


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
