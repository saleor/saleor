from django.apps import AppConfig
from django.db.models.signals import post_delete


class ProductAppConfig(AppConfig):
    name = "saleor.product"

    def ready(self):
        from .models import Category, Collection
        from .signals import delete_background_image

        post_delete.connect(
            delete_background_image,
            sender=Category,
            dispatch_uid="delete_category_background",
        )
        post_delete.connect(
            delete_background_image,
            sender=Collection,
            dispatch_uid="delete_collection_background",
        )
