from typing import Any

from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError
from django.core.management.base import CommandParser

from ....app.tasks import install_app_task
from ....app.validators import AppURLValidator
from ...installation_utils import fetch_manifest
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
        except ValidationError as e:
            raise CommandError(
                f"Incorrect format of manifest-url: {manifest_url}"
            ) from e

    def handle(self, *args: Any, **options: Any):
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

        install_app_task(app_job.id, activate=activate)
