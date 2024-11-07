from collections import defaultdict
from typing import Any

from django.utils import timezone
from promise import Promise

from ....core.db.connection import allow_writer_in_context
from ....tax import TaxCalculationStrategy
from ....tax.utils import (
    get_tax_app_id,
    get_tax_calculation_strategy,
    get_tax_configuration_for_checkout,
)
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.utils import get_webhooks_for_event
from ...app.dataloaders import AppByIdLoader
from ...checkout.dataloaders import (
    CheckoutInfoByCheckoutTokenLoader,
    CheckoutLinesInfoByCheckoutTokenLoader,
)
from ...core.dataloaders import DataLoader
from ...utils import get_user_or_app_from_context
from ..subscription_payload import (
    generate_payload_promise_from_subscription,
    initialize_request,
)
from ..utils import get_subscription_query_hash


class PregeneratedCheckoutTaxPayloadsByCheckoutTokenLoader(DataLoader):
    context_key = "pregenerated_checkout_tax_payloads_by_checkout_token"

    def batch_load(self, keys):
        """Fetch pregenerated tax payloads for checkouts.

        This loader is used to fetch pregenerated tax payloads for checkouts.

        return: A dict of tax payloads for checkouts.

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

        event_type = WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
        requestor = get_user_or_app_from_context(self.context)
        request_context = initialize_request(
            requestor,
            sync_event=True,
            allow_replica=False,
            event_type=event_type,
        )
        webhooks = get_webhooks_for_event(event_type)
        apps_ids = [webhook.app_id for webhook in webhooks]

        @allow_writer_in_context(self.context)
        def generate_payloads(data):
            checkouts_info, checkout_lines_info, apps = data
            apps_map = {app.id: app for app in apps}
            promises = []
            for checkout_info, lines_info in zip(checkouts_info, checkout_lines_info):
                tax_configuration, country_tax_configuration = (
                    get_tax_configuration_for_checkout(
                        checkout_info, lines_info, self.database_connection_name
                    )
                )
                tax_strategy = get_tax_calculation_strategy(
                    tax_configuration, country_tax_configuration
                )

                if (
                    tax_strategy == TaxCalculationStrategy.TAX_APP
                    and checkout_info.checkout.price_expiration <= timezone.now()
                ):
                    tax_app_identifier = get_tax_app_id(
                        tax_configuration, country_tax_configuration
                    )
                    for webhook in webhooks:
                        app_id = webhook.app_id
                        app = apps_map[app_id]
                        if webhook.subscription_query and (
                            not tax_app_identifier
                            or app.identifier == tax_app_identifier
                        ):
                            query_hash = get_subscription_query_hash(
                                webhook.subscription_query
                            )
                            checkout = checkout_info.checkout
                            checkout_token = str(checkout.token)

                            promise_payload = (
                                generate_payload_promise_from_subscription(
                                    event_type=event_type,
                                    subscribable_object=checkout,
                                    subscription_query=webhook.subscription_query,
                                    request=request_context,
                                    app=app,
                                )
                            )
                            promises.append(promise_payload)

                            def store_payload(
                                payload,
                                checkout_token=checkout_token,
                                app_id=app_id,
                                query_hash=query_hash,
                            ):
                                if payload:
                                    results[checkout_token][app_id][query_hash] = (
                                        payload
                                    )

                            promise_payload.then(store_payload)

            def return_payloads(_payloads):
                return [results[str(checkout_token)] for checkout_token in keys]

            return Promise.all(promises).then(return_payloads)

        checkouts_info = CheckoutInfoByCheckoutTokenLoader(self.context).load_many(keys)
        lines = CheckoutLinesInfoByCheckoutTokenLoader(self.context).load_many(keys)
        apps = AppByIdLoader(self.context).load_many(apps_ids)
        return Promise.all([checkouts_info, lines, apps]).then(generate_payloads)
