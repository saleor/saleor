import hashlib
import logging
from contextlib import contextmanager
import urllib
import urllib.parse

import requests
from django.conf import settings
from django.utils import timezone
from requests import Response

from .consts import PROCESS_URL
from ....core.tracing import opentracing_trace

logger = logging.getLogger(__name__)

@contextmanager
def payfast_opentracing_trace(span_name):
    with opentracing_trace(
        span_name=span_name, component_name="payment", service_name="stripe"
    ):
        yield


def _generate_signature(merchant_passphrase: str, payload: dict) -> str:
    """
    Generate the signature salted with the passphrase.
    https://developers.payfast.co.za/api#authentication
    :param merchant_passphrase:
    :param payload:
    :return: signature
    """
    payload_response = ""
    payload["passphrase"] = merchant_passphrase
    sorted_payload_keys = sorted(payload)
    for key in sorted_payload_keys:
        # Get all the data for PayFast and prepare parameter string
        payload_response += key + "=" + urllib.parse.quote_plus(str(payload[key])) + "&"
    # After looping through remove the last &
    del payload["passphrase"]
    payload_response = payload_response[:-1]
    return hashlib.md5(payload_response.encode()).hexdigest()


def _get_headers(merchant_id: str):
    """
    Generate
    the
    required
    headers.
    These
    are:
    - merchant - id
    - version
    - timestamp
    Does
    not include
    signature
    :return:
    """
    return {
        "timestamp": str(timezone.now()),
        "merchant-id": merchant_id,
        "version": "v1",
    }


def _send_post_request(path: str, passphrase: str, params: dict,
                       body: dict) -> Response:
    if settings.DEBUG:
        params["testing"] = "true"
    headers = _get_headers(body["merchant_id"])
    headers["signature"] = _generate_signature(passphrase, {**headers, **body})
    headers["content-type"] = "application/x-www-form-urlencoded"
    return requests.post(path, headers=headers, data=body, params=params)


def initiate_payment(base_url: str, passphrase: str, payment_data: dict):
    try:
        with payfast_opentracing_trace("payfast.Payment.create"):
            response = _send_post_request(f'{base_url}/{PROCESS_URL}',
                                          passphrase, params={},
                                          body=payment_data)
            return response
    except Exception as error:
        logger.warning(
            f"Failed to create Payfast payment\n{error}"
        )
        return None
