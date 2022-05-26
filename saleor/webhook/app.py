from django.apps import AppConfig


class WebhookAppConfig(AppConfig):
    name = "saleor.webhook"

    def ready(self):
        from django.conf import settings

        from .observability.worker import init

        if settings.OBSERVABILITY_ACTIVE:
            init()
