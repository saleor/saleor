import json
from typing import Any, Dict, List, Optional

import requests
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.core.management import BaseCommand, CommandError
from django.core.management.base import CommandParser
from requests.exceptions import RequestException

from ....core.permissions import get_permissions, get_permissions_enum_list
from ...models import ServiceAccount


class Command(BaseCommand):
    help = "Used to create service account."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("name", type=str)
        parser.add_argument(
            "--permission",
            action="append",
            default=[],
            dest="permissions",
            help="Assign new permission to Service Account. "
            "Argument can be specified multiple times.",
        )
        parser.add_argument("--is_active", default=True, dest="is_active")
        parser.add_argument(
            "--target_url",
            dest="target_url",
            help="Url which will receive newly created data of service account object. "
            "Command doesn't return service account data to stdout when this "
            "argument is provided.",
        )

    def validate_permissions(self, required_permissions: List[str]):
        permissions = [perm[1] for perm in get_permissions_enum_list()]
        for perm in required_permissions:
            if perm not in permissions:
                raise CommandError(
                    f"Permisssion: {perm} doesn't exist in Saleor."
                    f" Avaiable permissions: {permissions}"
                )

    def clean_permissions(self, required_permissions: List[str]) -> List[Permission]:
        permissions = get_permissions(required_permissions)
        return permissions

    def send_service_account_data(self, target_url, data: Dict[str, Any]):
        domain = Site.objects.get_current().domain
        headers = {"x-saleor-domain": domain}
        try:
            response = requests.post(target_url, json=data, headers=headers, timeout=15)
        except RequestException as e:
            raise CommandError(f"Request failed. Exception: {e}")
        if response.status_code != 200:
            raise CommandError(
                f"Failed to send service account data to {target_url}. "  # type: ignore
                f"Status code: {response.status_code}, content: {response.content}"
            )

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        name = options["name"]
        is_active = options["is_active"]
        target_url = options["target_url"]
        permissions = list(set(options["permissions"]))
        self.validate_permissions(permissions)

        service_account = ServiceAccount.objects.create(name=name, is_active=is_active)
        permissions_qs = self.clean_permissions(permissions)
        service_account.permissions.add(*permissions_qs)
        token_obj = service_account.tokens.create()
        data = {
            "auth_token": token_obj.auth_token,
        }
        if target_url:
            self.send_service_account_data(target_url, data)

        return json.dumps(data) if not target_url else ""
