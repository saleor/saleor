from django.apps import AppConfig
from django.db.models.signals import post_delete


class AttributeAppConfig(AppConfig):
    name = "saleor.attribute"

    def ready(self):
        from .models import AttributeValue
        from .signals import delete_attribute_value_file

        post_delete.connect(
            delete_attribute_value_file,
            sender=AttributeValue,
            dispatch_uid="delete_attribute_value_file",
        )
