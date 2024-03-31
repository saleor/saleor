from typing import cast

import graphene
import jwt
from django.core.exceptions import ValidationError

from .....account import models, notifications, search
from .....account.error_codes import AccountErrorCode
from .....core.jwt import jwt_decode
from .....giftcard.utils import assign_user_gift_cards
from .....order.utils import match_orders_with_new_user
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventAsyncType
from ....channel.utils import clean_channel
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import User


class ConfirmEmailChange(BaseMutation):
    user = graphene.Field(User, description="A user instance with a new email.")

    class Arguments:
        token = graphene.String(
            description="A one-time token required to change the email.", required=True
        )
        channel = graphene.String(
            description=(
                "Slug of a channel which will be used to notify users. Optional when "
                "only one channel exists."
            )
        )

    class Meta:
        description = "Confirm the email change of the logged-in user."
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_UPDATED,
                description="A customer account was updated.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification that account email change was confirmed.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ACCOUNT_EMAIL_CHANGED,
                description="An account email was changed.",
            ),
        ]

    @classmethod
    def get_token_payload(cls, token):
        try:
            payload = jwt_decode(token)
        except jwt.PyJWTError:
            raise ValidationError(
                {
                    "token": ValidationError(
                        "Invalid or expired token.",
                        code=AccountErrorCode.JWT_INVALID_TOKEN.value,
                    )
                }
            )
        return payload

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, channel=None, token
    ):
        user = info.context.user
        user = cast(models.User, user)

        payload = cls.get_token_payload(token)
        new_email = payload["new_email"].lower()
        old_email = payload["old_email"]

        if models.User.objects.filter(email=new_email).exists():
            raise ValidationError(
                {
                    "new_email": ValidationError(
                        "Email is used by other user.",
                        code=AccountErrorCode.UNIQUE.value,
                    )
                }
            )

        user.email = new_email
        user.search_document = search.prepare_user_search_document_value(user)
        user.save(update_fields=["email", "search_document", "updated_at"])
        channel_slug = clean_channel(
            channel, error_class=AccountErrorCode, allow_replica=False
        ).slug

        cls.post_save_action(info, user, channel_slug, old_email)

        return ConfirmEmailChange(user=user)

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, channel_slug, old_email):
        assign_user_gift_cards(instance)
        match_orders_with_new_user(instance)
        manager = get_plugin_manager_promise(info.context).get()
        notifications.send_user_change_email_notification(
            old_email, instance, manager, channel_slug=channel_slug
        )
        cls.call_event(manager.customer_updated, instance)
        cls.call_event(manager.account_email_changed, instance)
