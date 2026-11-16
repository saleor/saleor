from typing import Any

from django.core.management import CommandError
from django.core.management.base import CommandParser

from ...saleor_api_url import notify_saleor_api_url_changed
from .utils import JSONLinesCommand


class Command(JSONLinesCommand):
    help = (
        "Send SALEOR_API_URL_CHANGED to apps. Run it before the public URL changes; "
        "delivery is asynchronous and best effort."
    )

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--new-public-url",
            required=True,
            help="Public URL after the change, e.g. https://new.example.com.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        try:
            change = notify_saleor_api_url_changed(options["new_public_url"])
        except ValueError as e:
            raise CommandError(str(e)) from e
        self._write(
            {
                "kind": "saleor_api_url_change",
                "previous_saleor_api_url": change.previous_saleor_api_url,
                "saleor_api_url": change.saleor_api_url,
            }
        )
