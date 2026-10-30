from typing import Any

import graphene
from django.db.models import Prefetch

from ....core.utils.url import sanitize_url_for_logging
from ....webhook.models import Webhook
from ...models import App
from .utils import JSONLinesCommand


class Command(JSONLinesCommand):
    help = (
        "List apps that are not soft-deleted, each followed by its webhooks, "
        "as JSON Lines. Inactive apps and webhooks are included."
    )

    def handle(self, *args: Any, **options: Any) -> None:
        webhooks = Webhook.objects.order_by("pk").only(
            "pk", "app_id", "name", "target_url", "is_active"
        )
        apps = (
            App.objects.not_removed()
            .order_by("pk")
            .only("pk", "identifier", "name", "is_active")
            .prefetch_related(Prefetch("webhooks", queryset=webhooks))
        )
        for app in apps.iterator(chunk_size=1000):
            app_id = graphene.Node.to_global_id("App", app.pk)
            self._write(
                {
                    "kind": "app",
                    "id": app_id,
                    "identifier": app.identifier,
                    "name": app.name,
                    "is_active": app.is_active,
                }
            )
            # .all(), not .iterator(): iterator() bypasses the prefetch cache
            # and would run one query per app.
            for webhook in app.webhooks.all():
                self._write(
                    {
                        "kind": "webhook",
                        "id": graphene.Node.to_global_id("Webhook", webhook.pk),
                        "app_id": app_id,
                        "name": webhook.name,
                        "target_url": sanitize_url_for_logging(
                            webhook.target_url,
                            strip_querystring=True,
                            strip_fragment=True,
                        ),
                        "is_active": webhook.is_active,
                        "app_is_active": app.is_active,
                        # Mirrors the is_active filters in saleor/webhook/utils.py.
                        # App lifecycle events skip the app check, so an inactive
                        # app still gets its own APP_STATUS_CHANGED/APP_DELETED.
                        "delivering": webhook.is_active and app.is_active,
                    }
                )
