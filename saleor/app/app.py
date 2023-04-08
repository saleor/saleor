from django.apps import AppConfig as DjangoAppConfig
from django.db.models.signals import post_delete


class AppConfig(DjangoAppConfig):
    name = "saleor.app"

    def ready(self):
        from .models import App, AppInstallation
        from .signals import delete_brand_images

        # preventing duplicate signals
        post_delete.connect(
            delete_brand_images,
            sender=App,
            dispatch_uid="delete_app_brand_images",
        )
        post_delete.connect(
            delete_brand_images,
            sender=AppInstallation,
            dispatch_uid="delete_app_installation_brand_images",
        )
