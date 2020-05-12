import json
from typing import Any, List, Optional

from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError
from django.core.management.base import CommandParser
from django.core.validators import URLValidator

from ....core import JobStatus
from ....core.permissions import get_permissions, get_permissions_enum_list
from ...installation_utils import install_app
from ...models import AppJob
from ...tasks import install_app_task


class Command(BaseCommand):
    help = "Used to create new app."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("name", type=str, help="Name of new app.")
        parser.add_argument("manifest-url", help="Url with app manifest.", type=str)
        parser.add_argument(
            "--permission",
            action="append",
            default=[],
            dest="permissions",
            help="Assign new permission to app."
            "Argument can be specified multiple times.",
        )
        parser.add_argument(
            "--activate-after-installation", action="store_true", dest="activate"
        )
        parser.add_argument(
            "--use-celery",
            action="store_true",
            help="Use celery do schedule installation task.",
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

    def validate_manifest_url(self, manifest_url: str):
        url_validator = URLValidator()
        try:
            url_validator(manifest_url)
        except ValidationError:
            raise CommandError(f"Incorrect format of manifest-url: {manifest_url}")

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        name = options["name"]
        activate = options["activate"]
        manifest_url = options["manifest-url"]
        use_celery = options["use_celery"]

        permissions = list(set(options["permissions"]))
        self.validate_permissions(permissions)
        self.validate_manifest_url(manifest_url)

        app_job = AppJob.objects.create(name=name, manifest_url=manifest_url)
        if permissions:
            permissions_qs = self.clean_permissions(permissions)
            app_job.permissions.set(permissions_qs)

        if use_celery:
            install_app_task.delay(app_job.pk, activate)
            return "Celery task has been scheduled."

        try:
            app = install_app(app_job, activate)
        except Exception as e:
            app_job.status = JobStatus.FAILED
            app_job.save()
            raise e
        token = app.tokens.first()
        return json.dumps({"auth_token": token.auth_token})
