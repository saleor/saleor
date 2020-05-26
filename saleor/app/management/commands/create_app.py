import json
from typing import Any, Dict, Optional

import requests
from django.contrib.sites.models import Site
from django.core.management import BaseCommand, CommandError
from django.core.management.base import CommandParser
from requests.exceptions import RequestException

from ...models import App
from .utils import clean_permissions


class Command(BaseCommand):
    help = "Used to create new app."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("name", type=str)
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
            help="Url which will receive newly created data of app object. "
            "Command doesn't return app data to stdout when this "
            "argument is provided.",
        )

    def send_app_data(self, target_url, data: Dict[str, Any]):
        domain = Site.objects.get_current().domain
        headers = {"x-saleor-domain": domain}
        try:
            response = requests.post(target_url, json=data, headers=headers, timeout=15)
        except RequestException as e:
            raise CommandError(f"Request failed. Exception: {e}")
        response.raise_for_status()

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        name = options["name"]
        is_active = options["activate"]
        target_url = options["target_url"]
        permissions = list(set(options["permissions"]))
        permissions = clean_permissions(permissions)
        app = App.objects.create(name=name, is_active=is_active)
        app.permissions.set(permissions)
        token_obj = app.tokens.create()
        data = {
            "auth_token": token_obj.auth_token,
        }
        if target_url:
            self.send_app_data(target_url, data)

        return json.dumps(data) if not target_url else ""
