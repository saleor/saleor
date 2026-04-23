from typing import Any

from django.core.management import BaseCommand
from django.core.management.base import CommandParser

from ....plugins.manager import get_plugins_manager
from ...actions import delete_app
from ...models import App


class Command(BaseCommand):
    help = (
        "Soft-delete every installed app. Iterates over all apps that have "
        "not been soft-deleted yet uses the same logic as appDelete mutation "
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--force-sync",
            dest="force_sync",
            action="store_true",
            help="Emit APP_DELETED synchronously instead of queueing on Celery.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        apps = list(App.objects.not_removed().order_by("pk"))
        if not apps:
            self.stdout.write("No active apps to delete.")
            return

        force_sync = options["force_sync"]
        manager = get_plugins_manager(allow_replica=False)
        for app in apps:
            delete_app(app, manager, force_sync=force_sync)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Deleted app pk={app.pk} identifier={app.identifier!r} "
                    f"name={app.name!r}."
                )
            )

        self.stdout.write(self.style.SUCCESS(f"Deleted {len(apps)} app(s)."))
