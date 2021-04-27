import json
from decimal import Decimal

import stripe
from django.contrib.sites.models import Site
from typing import List, Optional, Tuple
from django.urls import reverse
from stripe.error import StripeError, AuthenticationError
from stripe.stripe_object import StripeObject

import logging
from .consts import PLUGIN_ID, WEBHOOK_PATH, WEBHOOK_EVENTS, METADATA_IDENTIFIER
from urllib.parse import urlunparse, urljoin
from saleor.core.utils import build_absolute_uri
from ...utils import price_to_minor_unit
from typing import Callable

logger = logging.getLogger(__name__)


def is_secret_api_key_valid(api_key:str):
    """Call api to check if api_key is a correct key."""
    try:
        stripe.WebhookEndpoint.list(api_key)
        return True
    except AuthenticationError:
        return False


def subscribe_to_webhook(api_key: str) -> StripeObject:
    domain = Site.objects.get_current().domain
    api_path = reverse("plugins", kwargs={"plugin_id": PLUGIN_ID})

    base_url = build_absolute_uri(api_path)
    webhook_url = urljoin(base_url, WEBHOOK_PATH)

    return stripe.WebhookEndpoint.create(
        api_key=api_key,
        url=webhook_url,
        enabled_events=WEBHOOK_EVENTS,
        metadata={
            METADATA_IDENTIFIER: domain
        }
    )


def change_webhook_status(api_key: str, webhook_id:str, disabled:bool)->Optional[StripeObject]:
    try:
        return stripe.WebhookEndpoint.modify(
            webhook_id,
            disabled=disabled,
            api_key=api_key,
        )
    except StripeError:
        logger.warning("Unable to modify a webhook (%s) status to disabled: %s", webhook_id, disabled)
        return None


def enable_webhook(api_key: str, webhook_id:str) -> StripeObject:
    return change_webhook_status(api_key, webhook_id, disabled=False)


def disable_webhook(api_key: str, webhook_id:str) -> StripeObject:
    return change_webhook_status(api_key, webhook_id, disabled=True)


def retrieve_webhook(api_key: str, webhook_id: str) -> Optional[StripeObject]:
    try:
        return stripe.WebhookEndpoint.retrieve(webhook_id, api_key=api_key)
    except StripeError:
        logger.warning("Unable to retrieve a webhook (%s)", webhook_id)
        return None


def create_payment_intent(api_key: str, amount:Decimal, currency: str) -> Tuple[Optional[StripeObject], Optional[str]]:
    try:
        intent = stripe.PaymentIntent.create(
            api_key=api_key,
            amount=price_to_minor_unit(amount, currency),
            currency=currency
        )
        return intent, None
    except StripeError as e:
        error=json.dumps(e.json_body)

    return None, error


def retrieve_payment_intent(api_key: str, payment_intent_id:str)->Optional[StripeObject]:
    try:
        return stripe.PaymentIntent.retrieve(payment_intent_id, api_key=api_key)
    except StripeError:
        logger.warning("Unable to retrieve a payment intent (%s)", payment_intent_id)
        return None
