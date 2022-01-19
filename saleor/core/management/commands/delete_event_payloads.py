from django.core.management.base import BaseCommand

from ...tasks import delete_event_payloads_task


class Command(BaseCommand):
    help = (
        "Delete EventPayloads and EventDelivery from database "
        "that are older than the value set "
        "in EVENT_PAYLOAD_DELETE_PERIOD environment variable."
    )

    def handle(self, **options):
        delete_event_payloads_task()
