import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError

from .....account import models
from .....account.error_codes import AccountErrorCode
from .....core.tokens import token_generator
from .....giftcard.utils import assign_user_gift_cards
from .....order.utils import match_orders_with_new_user
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import User

INVALID_TOKEN = "Invalid or expired token."


class ConfirmAccount(BaseMutation):
    user = graphene.Field(User, description="An activated user account.")

    class Arguments:
        token = graphene.String(
            description="A one-time token required to confirm the account.",
            required=True,
        )
        email = graphene.String(
            description="E-mail of the user performing account confirmation.",
            required=True,
        )

    class Meta:
        description = (
            "Confirm user account with token sent by email during registration."
        )
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.ACCOUNT_CONFIRMED,
                description="Account was confirmed.",
            ),
        ]

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        error = False
        try:
            user = models.User.objects.get(email=data["email"])
        except ObjectDoesNotExist:
            # If user doesn't exists in the database we create fake user for calculation
            # purpose, as we don't want to indicate non existence of user in the system.
            error = True
            user = models.User()

        valid_token = token_generator.check_token(user, data["token"])
        if not valid_token or error:
            raise ValidationError(
                {
                    "token": ValidationError(
                        INVALID_TOKEN, code=AccountErrorCode.INVALID.value
                    )
                }
            )

        user.is_active = True
        user.is_confirmed = True
        user.save(update_fields=["is_active", "is_confirmed", "updated_at"])

        match_orders_with_new_user(user)
        assign_user_gift_cards(user)

        cls.post_save_action(info, user)

        return ConfirmAccount(user=user)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance):
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.account_confirmed, instance)
