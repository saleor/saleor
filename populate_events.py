# This script is used to populate the DB with EventDelivery and EventPayload objects,
# without the need of triggering webhooks manually. Should be removed after development,
# or moved into `populatedb` script if it is more useful.

import random

from saleor.app.models import App
from saleor.core.models import EventDelivery, EventPayload

RANGE = 100


def populate_events(count: int = RANGE):
    apps = App.objects.all()
    assert len(apps) >= 2

    webhooks = {
        "order_updated": apps[0].webhooks.first(),
        "product_updated": apps[1].webhooks.first(),
    }

    payloads = {
        "order_updated": '{"__typename": "OrderUpdated"}',
        "product_updated": '{"__typename": "ProductUpdated"}',
    }

    event_deliveries = []
    event_payloads = []
    event_payloads_data = []

    for _ in range(count):
        event_type = random.choice(["product_updated", "order_updated"])

        payload_data = payloads[event_type]
        event_payloads_data.append(payload_data)
        event_payload = EventPayload()
        event_payloads.append(event_payload)
        event_deliveries.append(
            EventDelivery(
                status="pending",
                event_type=event_type,
                payload=event_payload,
                webhook=webhooks[event_type],
            )
        )

    EventPayload.objects.bulk_create_with_payload_files(
        event_payloads, event_payloads_data
    )
    EventDelivery.objects.bulk_create(event_deliveries)


if __name__ == "__main__":
    populate_events()
