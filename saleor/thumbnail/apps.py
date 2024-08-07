from django.apps import AppConfig
from django.db.models.signals import post_delete


class ThumbnailAppConfig(AppConfig):
    name = "saleor.thumbnail"

    def ready(self):
        from .models import Thumbnail
        from .signals import delete_thumbnail_image

        post_delete.connect(
            delete_thumbnail_image,
            sender=Thumbnail,
            dispatch_uid="delete_thumbnail_image",
        )
