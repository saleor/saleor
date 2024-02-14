import json
from typing import Any, Optional

import graphene
from django.core.management import BaseCommand, CommandError
from django.core.management.base import CommandParser
from django.urls import reverse
from requests.exceptions import RequestException

from .... import schema_version
from ....app.headers import AppHeaders, DeprecatedAppHeaders
from ....core.http_client import HTTPClient
from ....core.utils import build_absolute_uri, get_domain
from ...models import App
from .utils import clean_permissions


class Command(BaseCommand):
    help = "Used to create new app."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("name", type=str)
        parser.add_argument(
            "--identifier",
            dest="identifier",
            default="",
            help=(
                "Canonical app ID. If not provided, "
                "the identifier will be generated based on app.id."
            ),
        )
        parser.add_argument(
            "--permission",
            action="append",
            default=[],
            dest="permissions",
            help="Assign new permission to app."
            "Argument can be specified multiple times.",
        )
        parser.add_argument(
            "--activate",
            action="store_true",
            dest="activate",
            help="Activates the app after installation",
        )
        parser.add_argument(
            "--target-url",
            dest="target_url",
            help="URL which will receive newly created data of app object. "
            "Command doesn't return app data to stdout when this "
            "argument is provided.",
        )

    def send_app_data(self, target_url, data: dict[str, Any]):
        domain = get_domain()
        headers = {
            # X- headers will be deprecated in Saleor 4.0, proper headers are without X-
            DeprecatedAppHeaders.DOMAIN: domain,
            AppHeaders.DOMAIN: domain,
            AppHeaders.API_URL: build_absolute_uri(reverse("api"), domain),
            AppHeaders.SCHEMA_VERSION: schema_version,
        }
        try:
            response = HTTPClient.send_request(
                "POST",
                target_url,
                json=data,
                headers=headers,
                allow_redirects=False,
            )
        except RequestException as e:
            raise CommandError(f"Request failed. Exception: {e}")
        response.raise_for_status()

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        name = options["name"]
        is_active = options["activate"]
        target_url = options["target_url"]
        identifier = options["identifier"]
        permissions = list(set(options["permissions"]))
        permissions = clean_permissions(permissions)
        app = App.objects.create(name=name, is_active=is_active, identifier=identifier)
        if not identifier:
            app.identifier = graphene.Node.to_global_id("App", app.pk)
            app.save(update_fields=["identifier"])
        app.permissions.set(permissions)
        _, auth_token = app.tokens.create()  # type: ignore[call-arg] # method of a related manager # noqa: E501
        data = {
            "auth_token": auth_token,
        }
        if target_url:
            self.send_app_data(target_url, data)

        return json.dumps(data) if not target_url else ""
