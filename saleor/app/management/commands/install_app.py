import json
from typing import Any, Optional

from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError
from django.core.management.base import CommandParser

from ....app.validators import AppURLValidator
from ....core import JobStatus
from ...installation_utils import fetch_manifest, install_app
from ...models import AppInstallation
from .utils import clean_permissions


class Command(BaseCommand):
    help = "Used to install new app."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("manifest-url", help="URL with app manifest.", type=str)
        parser.add_argument(
            "--activate",
            action="store_true",
            dest="activate",
            help="Activates the app after installation",
        )

    def validate_manifest_url(self, manifest_url: str):
        url_validator = AppURLValidator()
        try:
            url_validator(manifest_url)
        except ValidationError:
            raise CommandError(f"Incorrect format of manifest-url: {manifest_url}")

    def handle(self, *args: Any, **options: Any) -> Optional[str]:
        activate = options["activate"]
        manifest_url = options["manifest-url"]

        self.validate_manifest_url(manifest_url)
        manifest_data = fetch_manifest(manifest_url)

        permissions = clean_permissions(manifest_data.get("permissions", []))

        app_job = AppInstallation.objects.create(
            app_name=manifest_data["name"], manifest_url=manifest_url
        )
        if permissions:
            app_job.permissions.set(permissions)

        try:
            _, token = install_app(app_job, activate)
            app_job.delete()
        except Exception as e:
            app_job.status = JobStatus.FAILED
            app_job.save(update_fields=["status"])
            raise e
        return json.dumps({"auth_token": token})
