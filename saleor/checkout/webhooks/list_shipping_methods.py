import base64
import json
from collections.abc import Iterable
from typing import Any, Final, Optional

from django.conf import settings
from prices import Money

from ...app.models import App
from ...core.middleware import Requestor
from ...permission.enums import ShippingPermissions
from ...shipping.interface import ShippingMethodData
from ...webhook.base import SyncWebhookBase
from ...webhook.const import APP_ID_PREFIX
from ...webhook.utils import get_webhooks_for_event
from ..models import Checkout

# Set the timeout for the shipping methods cache to 12 hours as it was the lowest
# time labels were valid for when checking documentation for the carriers
# (FedEx, UPS, TNT, DHL).
CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT: Final[int] = 3600 * 12


def to_shipping_app_id(app: "App", shipping_method_id: str) -> "str":
    app_identifier = app.identifier or app.id
    return base64.b64encode(
        str.encode(f"{APP_ID_PREFIX}:{app_identifier}:{shipping_method_id}")
    ).decode("utf-8")


def convert_to_app_id_with_identifier(shipping_app_id: str):
    """Prepare the shipping_app_id in format `app:<app-identifier>/method_id>`.

    The format of shipping_app_id has been changes so we need to support both of them.
    This method is preparing the new shipping_app_id format based on assumptions
    that right now the old one is used which is `app:<app-pk>:method_id>`
    """
    decoded_id = base64.b64decode(shipping_app_id).decode()
    splitted_id = decoded_id.split(":")
    if len(splitted_id) != 3:
        return
    try:
        app_id = int(splitted_id[1])
    except (TypeError, ValueError):
        return None
    app = App.objects.filter(id=app_id).first()
    if app is None:
        return None
    return to_shipping_app_id(app, splitted_id[2])


def method_metadata_is_valid(metadata) -> bool:
    if not isinstance(metadata, dict):
        return False
    for key, value in metadata.items():
        if not isinstance(key, str) or not isinstance(value, str) or not key.strip():
            return False
    return True


def validate_shipping_method_data(shipping_method_data):
    if not isinstance(shipping_method_data, dict):
        return False
    keys = ["id", "name", "amount", "currency"]
    return all(key in shipping_method_data for key in keys)


def parse_list_shipping_methods_response(
    response_data: Any, app: "App"
) -> list["ShippingMethodData"]:
    shipping_methods = []
    for shipping_method_data in response_data:
        if not validate_shipping_method_data(shipping_method_data):
            continue
        method_id = shipping_method_data.get("id")
        method_name = shipping_method_data.get("name")
        method_amount = shipping_method_data.get("amount")
        method_currency = shipping_method_data.get("currency")
        method_maximum_delivery_days = shipping_method_data.get("maximum_delivery_days")
        method_minimum_delivery_days = shipping_method_data.get("minimum_delivery_days")
        method_description = shipping_method_data.get("description")
        method_metadata = shipping_method_data.get("metadata")
        if method_metadata:
            method_metadata = (
                method_metadata if method_metadata_is_valid(method_metadata) else {}
            )

        shipping_methods.append(
            ShippingMethodData(
                id=to_shipping_app_id(app, method_id),
                name=method_name,
                price=Money(method_amount, method_currency),
                maximum_delivery_days=method_maximum_delivery_days,
                minimum_delivery_days=method_minimum_delivery_days,
                description=method_description,
                metadata=method_metadata,
            )
        )
    return shipping_methods


def get_cache_data_for_shipping_list_methods_for_checkout(payload: str) -> dict:
    key_data = json.loads(payload)

    # drop fields that change between requests but are not relevant for cache key
    key_data[0].pop("last_change")
    key_data[0].pop("meta")
    # Drop the external_app_shipping_id from the cache key as it should not have an
    # impact on cache invalidation
    if "external_app_shipping_id" in key_data[0].get("private_metadata", {}):
        del key_data[0]["private_metadata"]["external_app_shipping_id"]
    return key_data


class ShippingListMethodsForCheckout(SyncWebhookBase):
    description = "Fetch external shipping methods for checkout."
    event_type = "shipping_list_methods_for_checkout"
    legacy_manager_func = None
    name = "List shipping methods for checkout"
    permission = ShippingPermissions.MANAGE_SHIPPING
    subscription_type = (
        "saleor.graphql.checkout.subscriptions.ShippingListMethodsForCheckout"
    )

    @classmethod
    def trigger_webhook(
        cls,
        checkout: Optional[Checkout],
        requestor: Optional[Requestor],
        allow_replica: bool = True,
    ) -> Iterable[ShippingMethodData]:
        from ...plugins.manager import get_plugins_manager
        from ...webhook.payloads import generate_checkout_payload
        from ...webhook.transport.synchronous.transport import (
            trigger_webhook_sync_if_not_cached,
        )

        webhooks = get_webhooks_for_event(cls)
        if not webhooks or not checkout:
            return []

        if settings.USE_LEGACY_WEBHOOK_PLUGIN:
            manager = get_plugins_manager(allow_replica)
            return manager.list_shipping_methods_for_checkout(
                checkout=checkout, channel_slug=checkout.channel.slug
            )

        methods = []

        payload = generate_checkout_payload(checkout, requestor)

        cache_data = get_cache_data_for_shipping_list_methods_for_checkout(payload)
        for webhook in webhooks:
            response_data = trigger_webhook_sync_if_not_cached(
                event_type=cls.event_type,
                payload=payload,
                webhook=webhook,
                cache_data=cache_data,
                allow_replica=allow_replica,
                subscribable_object=checkout,
                request_timeout=settings.WEBHOOK_SYNC_TIMEOUT,
                cache_timeout=CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT,
                requestor=requestor,
            )

            if response_data:
                shipping_methods = parse_list_shipping_methods_response(
                    response_data, webhook.app
                )
                methods.extend(shipping_methods)
        return methods
