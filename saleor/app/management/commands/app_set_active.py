import json
from typing import Any

import graphene
from django.core.management import BaseCommand, CommandError
from django.core.management.base import CommandParser

from ....core.tracing import traced_atomic_transaction
from ....core.utils.events import call_event
from ....plugins.manager import get_plugins_manager
from ...lock_objects import app_qs_select_for_update
from .utils import decode_global_id, parse_bool


class Command(BaseCommand):
    help = (
        "Activate or deactivate an app, like the appActivate/appDeactivate "
        "mutations. Does nothing when the app is already in the target state."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--id", required=True, help="App global ID.")
        parser.add_argument(
            "--active", required=True, type=parse_bool, help="true or false."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        global_id = options["id"]
        target = options["active"]
        pk = decode_global_id(global_id, "App")
        with traced_atomic_transaction():
            app = (
                app_qs_select_for_update()
                .filter(pk=pk, removed_at__isnull=True)
                .first()
            )
            if app is None:
                raise CommandError(f"App not found: {global_id}.")
            before = app.is_active
            if before != target:
                app.is_active = target
                app.save(update_fields=["is_active"])
                manager = get_plugins_manager(allow_replica=False)
                call_event(manager.app_status_changed, app)
        self.stdout.write(
            json.dumps(
                {
                    "kind": "app",
                    "id": graphene.Node.to_global_id("App", app.pk),
                    "identifier": app.identifier,
                    "name": app.name,
                    "is_active": {"before": before, "after": target},
                }
            )
        )
