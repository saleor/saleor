from django.apps import AppConfig
from django.db.models.signals import post_delete


class ProductAppConfig(AppConfig):
    name = "saleor.product"

    def ready(self):
        from .models import Category, Collection, DigitalContent
        from .signals import delete_background_image, delete_digital_content_file

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
        post_delete.connect(
            delete_digital_content_file,
            sender=DigitalContent,
            dispatch_uid="delete_digital_content_file",
        )
