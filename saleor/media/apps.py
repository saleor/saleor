from django.apps import AppConfig
from django.db.models.signals import post_delete


class MediaConfig(AppConfig):
    name = "saleor.media"

    def ready(self):
        from .models import CategoryMedia, CollectionMedia, PageMedia, ProductMedia
        from .signals import delete_media_image

        for model in (ProductMedia, CategoryMedia, CollectionMedia, PageMedia):
            post_delete.connect(
                delete_media_image,
                sender=model,
                dispatch_uid=f"delete_{model._meta.model_name}_image",
            )
