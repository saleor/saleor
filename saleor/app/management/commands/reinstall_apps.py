from typing import Any

from django.core.management import BaseCommand

from ...installation_utils import reinstall_app
from ...models import App
from ...tasks import install_app_task
from ...types import AppType


class Command(BaseCommand):
    help = "Used to reinstall installed apps."

    def handle(self, *args: Any, **options: Any):
        # deactivate local apps
        App.objects.filter(type=AppType.LOCAL).update(is_active=False)

        # reinstall and deactivate thirdparty apps
        apps = App.objects.filter(type=AppType.THIRDPARTY)
        for app in apps:
            try:
                app_installation = reinstall_app(app)
                install_app_task.delay(app_installation.pk, False)
            except ValueError:
                app.is_active = False
                app.save(update_fields=["is_active"])
