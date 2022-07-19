from django.apps import AppConfig
from django.db.models.signals import post_delete, pre_delete


class ProductAppConfig(AppConfig):
    name = "saleor.product"

    def ready(self):
        from .models import Category, Collection, DigitalContent, Product, ProductMedia
        from .signals import (
            delete_background_image,
            delete_digital_content_file,
            delete_product_all_media,
            delete_product_media_image,
        )

        # preventing duplicate signals
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
            delete_product_media_image,
            sender=ProductMedia,
            dispatch_uid="delete_product_media_image",
        )
        post_delete.connect(
            delete_digital_content_file,
            sender=DigitalContent,
            dispatch_uid="delete_digital_content_file",
        )
        pre_delete.connect(
            delete_product_all_media,
            sender=Product,
            dispatch_uid="delete_product_all_media",
        )
