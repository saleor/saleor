import logging
from decimal import Decimal
from typing import Optional, Tuple
from urllib.parse import urljoin

import stripe
from django.contrib.sites.models import Site
from django.urls import reverse
from stripe.error import AuthenticationError, InvalidRequestError, StripeError
from stripe.stripe_object import StripeObject

from saleor.core.utils import build_absolute_uri

from ...utils import price_to_minor_unit
from .consts import METADATA_IDENTIFIER, PLUGIN_ID, WEBHOOK_EVENTS, WEBHOOK_PATH

logger = logging.getLogger(__name__)


def is_secret_api_key_valid(api_key: str):
    """Call api to check if api_key is a correct key."""
    try:
        stripe.WebhookEndpoint.list(api_key)
        return True
    except AuthenticationError:
        return False


def subscribe_webhook(api_key: str) -> StripeObject:
    domain = Site.objects.get_current().domain
    api_path = reverse("plugins", kwargs={"plugin_id": PLUGIN_ID})

    base_url = build_absolute_uri(api_path)
    webhook_url = urljoin(base_url, WEBHOOK_PATH)  # type: ignore

    return stripe.WebhookEndpoint.create(
        api_key=api_key,
        url=webhook_url,
        enabled_events=WEBHOOK_EVENTS,
        metadata={METADATA_IDENTIFIER: domain},
    )


def delete_webhook(api_key: str, webhook_id: str):
    try:
        stripe.WebhookEndpoint.delete(webhook_id, api_key=api_key)
    except InvalidRequestError:
        # webhook doesn't exist
        pass


def create_payment_intent(
    api_key: str, amount: Decimal, currency: str
) -> Tuple[Optional[StripeObject], Optional[str]]:
    try:
        intent = stripe.PaymentIntent.create(
            api_key=api_key,
            amount=price_to_minor_unit(amount, currency),
            currency=currency,
        )
        return intent, None
    except StripeError as e:
        error = e.json_body

    return None, error


def retrieve_payment_intent(
    api_key: str, payment_intent_id: str
) -> Tuple[Optional[StripeObject], Optional[str]]:
    try:
        payment_intent = stripe.PaymentIntent.retrieve(
            payment_intent_id, api_key=api_key
        )
        return payment_intent, None
    except StripeError as e:
        error = e.json_body
        logger.warning("Unable to retrieve a payment intent (%s)", payment_intent_id)
        return None, error


def construct_stripe_event(
    api_key: str, payload: bytes, sig_header: str, endpoint_secret: str
) -> StripeObject:
    return stripe.Webhook.construct_event(
        payload, sig_header, endpoint_secret, api_key=api_key
    )
