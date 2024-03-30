from typing import cast
from urllib.parse import urlencode

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError

from .....account import models, notifications
from .....account.error_codes import AccountErrorCode
from .....core.jwt import create_token
from .....core.utils.url import prepare_url, validate_storefront_url
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


class RequestEmailChange(BaseMutation):
    user = graphene.Field(User, description="A user instance.")

    class Arguments:
        password = graphene.String(required=True, description="User password.")
        new_email = graphene.String(required=True, description="New user email.")
        redirect_url = graphene.String(
            required=True,
            description=(
                "URL of a view where users should be redirected to "
                "update the email address. URL in RFC 1808 format."
            ),
        )
        channel = graphene.String(
            description=(
                "Slug of a channel which will be used to notify users. Optional when "
                "only one channel exists."
            )
        )

    class Meta:
        description = "Request email change of the logged in user."
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for account email change.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ACCOUNT_CHANGE_EMAIL_REQUESTED,
                description="An account email change was requested.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        channel=None,
        new_email,
        password,
        redirect_url,
    ):
        user = info.context.user
        user = cast(models.User, user)
        new_email = new_email.lower()

        if not user.check_password(password):
            raise ValidationError(
                {
                    "password": ValidationError(
                        "Password isn't valid.",
                        code=AccountErrorCode.INVALID_CREDENTIALS.value,
                    )
                }
            )
        if models.User.objects.filter(email=new_email).exists():
            raise ValidationError(
                {
                    "new_email": ValidationError(
                        "Email is used by other user.",
                        code=AccountErrorCode.UNIQUE.value,
                    )
                }
            )
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error}, code=AccountErrorCode.INVALID.value
            )
        channel_slug = clean_channel(
            channel, error_class=AccountErrorCode, allow_replica=False
        ).slug

        token_payload = {
            "old_email": user.email,
            "new_email": new_email,
            "user_pk": user.pk,
        }
        token = create_token(token_payload, settings.JWT_TTL_REQUEST_EMAIL_CHANGE)
        manager = get_plugin_manager_promise(info.context).get()
        params = urlencode({"token": token})

        # Notifications will be deprecated in the future
        notifications.send_request_user_change_email_notification(
            redirect_url,
            user,
            new_email,
            token,
            manager,
            channel_slug=channel_slug,
        )

        cls.call_event(
            manager.account_change_email_requested,
            user,
            channel_slug,
            token,
            prepare_url(params, redirect_url),
            new_email,
        )

        return RequestEmailChange(user=user)
