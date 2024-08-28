from collections.abc import Iterable
from typing import Final, Optional

from django.conf import settings

from ...core.middleware import Requestor
from ...permission.enums import ShippingPermissions
from ...shipping.interface import ShippingMethodData
from ...webhook.base import SyncWebhookBase
from ...webhook.utils import get_webhooks_for_event
from ..models import Checkout

# Set the timeout for the shipping methods cache to 12 hours as it was the lowest
# time labels were valid for when checking documentation for the carriers
# (FedEx, UPS, TNT, DHL).
CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT: Final[int] = 3600 * 12


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
        from ...webhook.transport.shipping import (
            get_cache_data_for_shipping_list_methods_for_checkout,
            parse_list_shipping_methods_response,
        )
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
