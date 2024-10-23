from collections import defaultdict
from typing import Any

from promise import Promise

from ....webhook.event_types import WebhookEventSyncType
from ...app.dataloaders.apps import AppsByEventTypeLoader
from ...checkout.dataloaders.models import CheckoutByTokenLoader
from ...core.dataloaders import DataLoader
from ..subscription_payload import (
    generate_payload_promise_from_subscription,
)
from ..utils import get_subscription_query_hash
from .models import WebhooksByEventTypeLoader
from .request_context import (
    PayloadsRequestContextByEventTypeLoader,
)


class PregeneratedCheckoutFilterShippingMethodPayloadsByCheckoutTokenLoader(DataLoader):
    context_key = (
        "pregenerated_checkout_filter_shipping_method_payloads_by_checkout_token"
    )

    def batch_load(self, keys):
        """Fetch pregenerated tax payloads for checkout shipping method filtering.

        This loader is used to fetch pregenerated payloads for checkouts shipping method filtering.

        return: A dict of shipping method filtering payloads for checkouts.

        Example:
        {
            "checkout_token": {
                "app_id": {
                    "query_hash": {
                        <payload>
                    }
                }
            }
        }

        """

        results: dict[str, dict[int, dict[str, dict[str, Any]]]] = defaultdict(
            lambda: defaultdict(dict)
        )

        event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS

        def generate_payloads(data):
            checkouts, apps, request_context, webhooks = data
            apps_map = {app.id: app for app in apps}
            promises = []
            for checkout in checkouts:
                for webhook in webhooks:
                    if not webhook.subscription_query:
                        continue
                    query_hash = get_subscription_query_hash(webhook.subscription_query)
                    app_id = webhook.app_id
                    app = apps_map[app_id]
                    checkout_token = str(checkout.token)
                    promise_payload = generate_payload_promise_from_subscription(
                        event_type=event_type,
                        subscribable_object=checkout,
                        subscription_query=webhook.subscription_query,
                        request=request_context,
                        app=app,
                    )
                    promises.append(promise_payload)

                    def store_payload(
                        payload,
                        checkout_token=checkout_token,
                        app_id=app_id,
                        query_hash=query_hash,
                    ):
                        if payload:
                            results[checkout_token][app_id][query_hash] = payload

                    promise_payload.then(store_payload)

            def return_payloads(_payloads):
                return [results[str(checkout.token)] for checkout in checkouts]

            return Promise.all(promises).then(return_payloads)

        checkouts = CheckoutByTokenLoader(self.context).load_many(keys)
        apps = AppsByEventTypeLoader(self.context).load(event_type)
        request_context = PayloadsRequestContextByEventTypeLoader(self.context).load(
            event_type
        )
        webhooks = WebhooksByEventTypeLoader(self.context).load(event_type)
        return Promise.all([checkouts, apps, request_context, webhooks]).then(
            generate_payloads
        )
