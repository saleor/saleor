from django.core.management.base import BaseCommand
from pydantic import schema_json_of

from ....app.manifest_schema import Manifest
from ....webhook.event_types import WebhookEventSyncType
from ...taxes import TaxData

SCHEMA_MAP = {
    "manifest": Manifest,
    WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES: TaxData,
    WebhookEventSyncType.ORDER_CALCULATE_TAXES: TaxData,
}


class Command(BaseCommand):
    help = "Writes selected JSON-schema to stdout"

    def add_arguments(self, parser):
        parser.add_argument("event_type", type=str)

    def handle(self, *args, event_type: str, **kwargs):
        if model := SCHEMA_MAP.get(event_type.lower()):
            self.stdout.write(schema_json_of(model, indent=2))
        else:
            self.stderr.write(f"Error: Can't find schema for event: {event_type}")
