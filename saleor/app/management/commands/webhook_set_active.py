import json
from typing import Any

import graphene
from django.core.management import BaseCommand, CommandError
from django.core.management.base import CommandParser

from ....core.tracing import traced_atomic_transaction
from ....webhook.models import Webhook
from .utils import decode_global_id, parse_bool


class Command(BaseCommand):
    help = (
        "Activate or deactivate a webhook, like webhookUpdate(input: {isActive}). "
        "Does nothing when the webhook is already in the target state."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--id", required=True, help="Webhook global ID.")
        parser.add_argument(
            "--active", required=True, type=parse_bool, help="true or false."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        global_id = options["id"]
        target = options["active"]
        pk = decode_global_id(global_id, "Webhook")
        with traced_atomic_transaction():
            webhook = (
                Webhook.objects.select_for_update(of=["self"])
                .filter(pk=pk, app__removed_at__isnull=True)
                .first()
            )
            if webhook is None:
                raise CommandError(f"Webhook not found: {global_id}.")
            before = webhook.is_active
            if before != target:
                webhook.is_active = target
                webhook.save(update_fields=["is_active"])
        self.stdout.write(
            json.dumps(
                {
                    "kind": "webhook",
                    "id": graphene.Node.to_global_id("Webhook", webhook.pk),
                    "app_id": graphene.Node.to_global_id("App", webhook.app_id),
                    "name": webhook.name,
                    "is_active": {"before": before, "after": target},
                }
            )
        )
