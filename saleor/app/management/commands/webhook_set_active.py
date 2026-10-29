from typing import Any

import graphene
from django.core.management import CommandError
from django.core.management.base import CommandParser

from ....webhook.models import Webhook
from ...models import App
from .utils import JSONLinesCommand, parse_bool, parse_id


class Command(JSONLinesCommand):
    help = (
        "Activate or deactivate a webhook, like webhookUpdate(input: {isActive}). "
        "Does nothing when the webhook is already in the target state."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--id", required=True, help="Webhook database ID or GraphQL ID."
        )
        parser.add_argument(
            "--active", required=True, type=parse_bool, help="true or false."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        target = options["active"]
        pk = parse_id(options["id"], "Webhook")
        webhooks = Webhook.objects.filter(pk=pk, app__in=App.objects.not_removed())
        changed = webhooks.filter(is_active=not target).update(is_active=target)
        webhook = webhooks.first()
        if webhook is None:
            raise CommandError(f"Webhook not found: {options['id']}.")
        self._write(
            {
                "kind": "webhook",
                "id": graphene.Node.to_global_id("Webhook", webhook.pk),
                "app_id": graphene.Node.to_global_id("App", webhook.app_id),
                "name": webhook.name,
                "is_active": {
                    "before": not target if changed else webhook.is_active,
                    "after": webhook.is_active,
                },
            }
        )
