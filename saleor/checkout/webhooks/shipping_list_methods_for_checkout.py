from collections.abc import Iterable
from typing import Optional

from django.conf import settings

from ...core.middleware import Requestor
from ...permission.enums import ShippingPermissions
from ...shipping.interface import ShippingMethodData
from ...webhook.base import SyncWebhookBase
from ...webhook.const import CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT
from ...webhook.utils import get_webhooks_for_event
from ..models import Checkout


class ShippingListMethodsForCheckout(SyncWebhookBase):
    description = "Fetch external shipping methods for checkout."
    event_type = "shipping_list_methods_for_checkout"
    name = "List shipping methods for checkout"
    permission = ShippingPermissions.MANAGE_SHIPPING
    subscription_type = (
        "saleor.graphql.checkout.subscriptions.ShippingListMethodsForCheckout"
    )

    @classmethod
    def list_shipping_methods(
        cls,
        checkout: Checkout,
        requestor: Optional[Requestor] = None,
        allow_replica: bool = True,
    ) -> Iterable[ShippingMethodData]:
        """Fetch list of external shipping methods for checkout."""

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

    @classmethod
    def get_shipping_method(
        cls,
        shipping_method_id: str,
        checkout: Checkout,
        requestor: Optional[Requestor],
        allow_replica: bool = True,
    ) -> Optional[ShippingMethodData]:
        """Fetch a single external shipping method for checkout.

        This is a helper method that uses `shipping_list_methods_for_checkout` webhook
        underneath to fetch external shipping methods and get one by ID.
        """
        methods = {
            method.id: method
            for method in cls.list_shipping_methods(
                checkout=checkout, requestor=requestor, allow_replica=allow_replica
            )
        }
        return methods.get(shipping_method_id)
