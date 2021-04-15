from django.apps import AppConfig
from django.db.models.signals import post_delete


class AccountAppConfig(AppConfig):
    name = "saleor.account"

    def ready(self):
        from .models import User
        from .signals import delete_avatar

        post_delete.connect(
            delete_avatar,
            sender=User,
            dispatch_uid="delete_user_avatar",
        )
