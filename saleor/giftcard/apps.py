from django.apps import AppConfig
from django.db.models.signals import pre_delete


class GiftcardAppConfig(AppConfig):
    name = "saleor.giftcard"

    def ready(self):
        from ..account.models import User
        from .signals import deactivate_user_gift_cards

        pre_delete.connect(
            deactivate_user_gift_cards,
            sender=User,
            dispatch_uid="deactivate_user_gift_cards",
        )
