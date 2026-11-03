from typing import Any

import graphene
from django.core.management import CommandError
from django.core.management.base import CommandParser

from ....core.utils.events import call_event
from ....plugins.manager import get_plugins_manager
from ...models import App
from .utils import JSONLinesCommand, parse_bool, parse_id


class Command(JSONLinesCommand):
    help = (
        "Activate or deactivate an app, like the appActivate/appDeactivate "
        "mutations. Does nothing when the app is already in the target state."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--id", required=True, help="App database ID or GraphQL ID."
        )
        parser.add_argument(
            "--active", required=True, type=parse_bool, help="true or false."
        )

    def handle(self, *args: Any, **options: Any) -> None:
        target = options["active"]
        pk = parse_id(options["id"], "App")
        apps = App.objects.not_removed().filter(pk=pk)
        changed = apps.filter(is_active=not target).update(is_active=target)
        app = apps.first()
        if app is None:
            raise CommandError(f"App not found: {options['id']}.")
        if changed:
            manager = get_plugins_manager(allow_replica=False)
            call_event(manager.app_status_changed, app)
        self._write(
            {
                "kind": "app",
                "id": graphene.Node.to_global_id("App", app.pk),
                "identifier": app.identifier,
                "name": app.name,
                "is_active": {
                    "before": not target if changed else app.is_active,
                    "after": app.is_active,
                },
            }
        )
