from urllib.parse import urlencode

import graphene
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils import timezone

from .....account.error_codes import AccountErrorCode
from .....account.notifications import send_password_reset_notification
from .....account.utils import retrieve_user_by_email
from .....core.utils.url import prepare_url, validate_storefront_url
from .....webhook.event_types import WebhookEventAsyncType
from ....channel.utils import clean_channel, validate_channel
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ....site.dataloaders import get_site_promise


class RequestPasswordReset(BaseMutation):
    class Arguments:
        email = graphene.String(
            required=True,
            description="Email of the user that will be used for password recovery.",
        )
        redirect_url = graphene.String(
            required=True,
            description=(
                "URL of a view where users should be redirected to "
                "reset the password. URL in RFC 1808 format."
            ),
        )
        channel = graphene.String(
            description=(
                "Slug of a channel which will be used for notify user. Optional when "
                "only one channel exists."
            )
        )

    class Meta:
        description = "Sends an email with the account password modification link."
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for password reset.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ACCOUNT_SET_PASSWORD_REQUESTED,
                description="Setting a new password for the account is requested.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.STAFF_SET_PASSWORD_REQUESTED,
                description=(
                    "Setting a new password for the staff account is requested."
                ),
            ),
        ]

    @classmethod
    def clean_user(cls, email, redirect_url, info: ResolveInfo):
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error}, code=AccountErrorCode.INVALID.value
            )

        site = get_site_promise(info.context).get()
        user = retrieve_user_by_email(email)
        if not user:
            raise ValidationError(
                {
                    "email": ValidationError(
                        "User with this email doesn't exist",
                        code=AccountErrorCode.NOT_FOUND.value,
                    )
                }
            )

        if not user.can_login(site.settings):
            raise ValidationError(
                {
                    "email": ValidationError(
                        "User with this email is inactive",
                        code=AccountErrorCode.INACTIVE.value,
                    )
                }
            )

        if password_reset_time := user.last_password_reset_request:
            delta = timezone.now() - password_reset_time
            if delta.total_seconds() < settings.RESET_PASSWORD_LOCK_TIME:
                raise ValidationError(
                    {
                        "email": ValidationError(
                            "Password reset already requested",
                            code=AccountErrorCode.PASSWORD_RESET_ALREADY_REQUESTED.value,
                        )
                    }
                )

        return user

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        email = data["email"]
        redirect_url = data["redirect_url"]
        user = cls.clean_user(email, redirect_url, info)
        channel_slug = data.get("channel")
        token = default_token_generator.make_token(user)
        params = urlencode({"email": user.email, "token": token})

        if not user.is_staff:
            channel_slug = clean_channel(
                channel_slug, error_class=AccountErrorCode
            ).slug
        elif channel_slug is not None:
            channel_slug = validate_channel(
                channel_slug, error_class=AccountErrorCode
            ).slug

        manager = get_plugin_manager_promise(info.context).get()
        send_password_reset_notification(
            redirect_url,
            user,
            manager,
            channel_slug=channel_slug,
            staff=user.is_staff,
        )
        if user.is_staff:
            cls.call_event(
                manager.staff_set_password_requested,
                user,
                channel_slug,
                token,
                prepare_url(params, redirect_url),
            )
        else:
            cls.call_event(
                manager.account_set_password_requested,
                user,
                channel_slug,
                token,
                prepare_url(params, redirect_url),
            )

        user.last_password_reset_request = timezone.now()
        user.save(update_fields=["last_password_reset_request"])

        return RequestPasswordReset()
