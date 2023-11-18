from unittest import mock

import pytest
from requests_hardened import HTTPSession

from saleor.payment import PaymentError
from saleor.payment.gateways.adyen.utils.apple_pay import (
    initialize_apple_pay_session,
    validate_payment_data_for_apple_pay,
)


@pytest.mark.parametrize(
    ("validation_url", "merchant_identifier", "domain", "display_name", "certificate"),
    [
        (
            "https://apple-pay-gateway.apple.com/paymentservices/startSession",
            "merchant.com.identifier",
            "saleor.com",
            None,
            "certifiate data",
        ),
        (None, "merchant.com.identifier", "saleor.com", "Saleor", "certifiate data"),
        (
            "https://apple-pay-gateway.apple.com/paymentservices/startSession",
            None,
            "saleor.com",
            "Saleor",
            "certifiate data",
        ),
        (
            "https://apple-pay-gateway.apple.com/paymentservices/startSession",
            "merchant.com.identifier",
            None,
            "Saleor",
            "certifiate data",
        ),
        (
            "https://not-whitelisted-domain.com/paymentservices/startSession",
            "merchant.com.identifier",
            "saleor.com",
            "Saleor",
            "certifiate data",
        ),
        (
            "https://apple-pay-gateway.apple.com/paymentservices/startSession",
            "merchant.com.identifier",
            "saleor.com",
            "Saleor",
            None,
        ),
    ],
)
def test_validate_payment_data_for_apple_pay_raises_payment_error(
    validation_url, merchant_identifier, domain, display_name, certificate
):
    with pytest.raises(PaymentError):
        validate_payment_data_for_apple_pay(
            validation_url, merchant_identifier, domain, display_name, certificate
        )


def test_validate_payment_data_for_apple_pay():
    validation_url = "https://apple-pay-gateway.apple.com/paymentservices/startSession"
    merchant_identifier = "merchant.com.identifier"
    domain = "saleor.com"
    display_name = "Saleor "
    certificate = "certifiate data"

    validate_payment_data_for_apple_pay(
        validation_url, merchant_identifier, domain, display_name, certificate
    )


@mock.patch("saleor.payment.gateways.adyen.utils.apple_pay.NamedTemporaryFile")
@mock.patch.object(HTTPSession, "request")
def test_initialize_payment_for_apple_pay(mocked_request, mocked_tmp_file):
    mocked_cert_file_name = "cert-file-name"
    mocked_file = mock.MagicMock()
    mocked_file.__enter__.return_value = mocked_file
    mocked_file.name = mocked_cert_file_name
    mocked_tmp_file.return_value = mocked_file

    mocked_response = mock.Mock()
    mocked_response.ok = True
    mocked_response.json.return_value = {
        "epochTimestamp": 1604652056653,
        "expiresAt": 1604655656653,
        "merchantSessionIdentifier": "SSH5EFCB46BA25C4B14B3F37795A7F5B974_BB8E",
    }
    mocked_request.return_value = mocked_response

    validation_url = "https://apple-pay-gateway.apple.com/paymentservices/startSession"
    merchant_identifier = "merchant.com.identifier"
    domain = "saleor.com"
    display_name = "Saleor Shop"
    certificate = "certifiate data"

    initialize_apple_pay_session(
        validation_url,
        merchant_identifier,
        domain,
        display_name,
        certificate,
    )

    expected_data = {
        "merchantIdentifier": merchant_identifier,
        "displayName": display_name,
        "initiative": "web",
        "initiativeContext": domain,
    }

    mocked_request.assert_called_with(
        "POST",
        validation_url,
        json=expected_data,
        cert=mocked_cert_file_name,
        allow_redirects=False,
    )


@mock.patch.object(HTTPSession, "request")
def test_initialize_payment_for_apple_pay_request_failed(mocked_request):
    mocked_response = mock.Mock()
    mocked_response.ok = False
    mocked_response.json.return_value = {}
    mocked_request.return_value = mocked_response

    validation_url = "https://apple-pay-gateway.apple.com/paymentservices/startSession"
    merchant_identifier = "merchant.com.identifier"
    domain = "saleor.com"
    display_name = "Saleor Shop"
    certificate = "certifiate data"

    with pytest.raises(PaymentError):
        initialize_apple_pay_session(
            validation_url,
            merchant_identifier,
            domain,
            display_name,
            certificate,
        )
