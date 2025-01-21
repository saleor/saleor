import logging
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit

import requests

from .....core.http_client import HTTPClient
from .... import PaymentError

# https://developer.apple.com/documentation/apple_pay_on_the_web/
# setting_up_your_server#3172427

APPLE_DOMAINS = [
    "apple-pay-gateway.apple.com",
    "cn-apple-pay-gateway.apple.com",
    "apple-pay-gateway-nc-pod1.apple.com",
    "apple-pay-gateway-nc-pod2.apple.com",
    "apple-pay-gateway-nc-pod3.apple.com",
    "apple-pay-gateway-nc-pod4.apple.com",
    "apple-pay-gateway-nc-pod5.apple.com",
    "apple-pay-gateway-pr-pod1.apple.com",
    "apple-pay-gateway-pr-pod2.apple.com",
    "apple-pay-gateway-pr-pod3.apple.com",
    "apple-pay-gateway-pr-pod4.apple.com",
    "apple-pay-gateway-pr-pod5.apple.com",
    "cn-apple-pay-gateway-sh-pod1.apple.com",
    "cn-apple-pay-gateway-sh-pod2.apple.com",
    "cn-apple-pay-gateway-sh-pod3.apple.com",
    "cn-apple-pay-gateway-tj-pod1.apple.com",
    "cn-apple-pay-gateway-tj-pod2.apple.com",
    "cn-apple-pay-gateway-tj-pod3.apple.com",
    "apple-pay-gateway-cert.apple.com",
    "cn-apple-pay-gateway-cert.apple.com",
]

logger = logging.getLogger(__name__)


def validate_payment_data_for_apple_pay(
    validation_url: str | None,
    merchant_identifier: str | None,
    domain: str | None,
    display_name: str | None,
    certificate,
):
    if not certificate:
        raise PaymentError("Support for Apple Pay on the web is disabled.")

    required_fields = [
        (validation_url, "validationUrl"),
        (merchant_identifier, "merchantIdentifier"),
        (domain, "domain"),
        (display_name, "displayName"),
    ]
    for field, name in required_fields:
        if not field:
            raise PaymentError(f"Missing {name} in the input data.")

    domain = urlsplit(validation_url).netloc
    if domain not in APPLE_DOMAINS:
        raise PaymentError(
            "The domain of the validation url is not defined as an Apple Pay domain."
        )


def initialize_apple_pay_session(
    validation_url: str,
    merchant_identifier: str,
    domain: str,
    display_name: str,
    certificate: str,
) -> dict:
    request_data = {
        "merchantIdentifier": merchant_identifier,
        "displayName": display_name,
        "initiative": "web",
        "initiativeContext": domain,
    }
    try:
        response = make_request_to_initialize_apple_pay(
            validation_url, request_data, certificate
        )
    except requests.exceptions.RequestException as e:
        logger.warning("Failed to fetch the Apple Pay session", exc_info=True)
        raise PaymentError(
            "Unable to create Apple Pay payment session. Make sure that input data "
            " and certificate are correct."
        ) from e
    if not response.ok:
        # FIXME: shouldn't we forward some details here?
        raise PaymentError(
            "Unable to create Apple Pay payment session. Make sure that input data "
            " and certificate are correct."
        )
    return response.json()


def make_request_to_initialize_apple_pay(
    validation_url: str, request_data: dict, certificate: str
):
    with NamedTemporaryFile() as f:
        f.write(certificate.encode())
        f.flush()  # ensure all data written
        return HTTPClient.send_request(
            "POST",
            validation_url,
            json=request_data,
            cert=f.name,
            allow_redirects=False,
        )


def initialize_apple_pay(payment_data: dict, certificate: str) -> dict:
    # The Apple Pay on the web requires additional step
    validation_url = payment_data.get("validationUrl", "")
    merchant_identifier = payment_data.get("merchantIdentifier", "")
    domain = payment_data.get("domain", "")
    display_name = payment_data.get("displayName", "")
    validate_payment_data_for_apple_pay(
        validation_url=validation_url,
        merchant_identifier=merchant_identifier,
        domain=domain,
        display_name=display_name,
        certificate=certificate,
    )
    return initialize_apple_pay_session(
        validation_url=validation_url,
        merchant_identifier=merchant_identifier,
        domain=domain,
        display_name=display_name,
        certificate=certificate,
    )
