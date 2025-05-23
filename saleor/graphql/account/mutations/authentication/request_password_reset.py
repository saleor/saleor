import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from .....account.error_codes import AccountErrorCode
from .....account.tasks import trigger_send_password_reset_notification
from .....account.utils import RequestorAwareContext, retrieve_user_by_email
from .....core.utils.url import validate_storefront_url
from .....webhook.event_types import WebhookEventAsyncType
from ....channel.utils import clean_channel
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo


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
                "Slug of a channel which will be used to notify the user. "
                "It is needed for customers, if not provided, the notification may not happen. "
                "Please note that mutation will not fail if the channel is not provided. "
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
    def clean_user(cls, email, redirect_url):
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as e:
            raise ValidationError(
                {"redirect_url": e}, code=AccountErrorCode.INVALID.value
            ) from e

        user = retrieve_user_by_email(email)
        if user and user.last_password_reset_request:
            delta = timezone.now() - user.last_password_reset_request
            if delta.total_seconds() < settings.RESET_PASSWORD_LOCK_TIME:
                user = None
        elif user and not user.is_active:
            user = None

        return user

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        email = data["email"]
        redirect_url = data["redirect_url"]
        user = cls.clean_user(email, redirect_url)
        channel = data.get("channel")

        # Catching exception for backwards compatibility
        # Previously channel_slug was validated and error returner, we don't want to
        # return error to end user to prevent user enumeration.
        # Exception catching should be removed after logic for default_channel is removed
        try:
            channel_slug = clean_channel(
                channel, error_class=AccountErrorCode, allow_replica=False
            ).slug
        except ValidationError:
            channel_slug = None

        trigger_send_password_reset_notification.delay(
            redirect_url=redirect_url,
            user_pk=user.pk if user else None,
            context_data=RequestorAwareContext.create_context_data(info.context),
            channel_slug=channel_slug,
        )

        return RequestPasswordReset()
