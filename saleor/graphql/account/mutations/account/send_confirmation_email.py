from typing import cast
from urllib.parse import urlencode

import graphene
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.utils import timezone

from .....account import models
from .....account.error_codes import SendConfirmationEmailErrorCode
from .....account.notifications import send_account_confirmation
from .....core.utils.url import prepare_url, validate_storefront_url
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventAsyncType
from ....channel.utils import clean_channel
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import SendConfirmationEmailError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ....site.dataloaders import get_site_promise


class SendConfirmationEmail(BaseMutation):
    class Arguments:
        redirect_url = graphene.String(
            required=True,
            description=(
                "Base of frontend URL that will be needed to create confirmation "
                "URL."
            ),
        )
        channel = graphene.String(
            required=True,
            description=("Slug of a channel which will be used for notify user."),
        )

    class Meta:
        description = (
            "Sends a notification confirmation." + ADDED_IN_315 + PREVIEW_FEATURE
        )
        doc_category = DOC_CATEGORY_USERS
        error_type_class = SendConfirmationEmailError
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for account confirmation.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ACCOUNT_CONFIRMATION_REQUESTED,
                description=(
                    "An account confirmation was requested. "
                    "This event is always sent regardless of settings."
                ),
            ),
        ]

    @classmethod
    def clean_user(cls, site, redirect_url, info: ResolveInfo):
        user = info.context.user
        user = cast(models.User, user)

        if user.is_confirmed or not site.settings.enable_account_confirmation_by_email:
            raise ValidationError(
                ValidationError(
                    "User is already confirmed",
                    code=SendConfirmationEmailErrorCode.ACCOUNT_CONFIRMED.value,
                )
            )

        if confirm_email_time := user.last_confirm_email_request:
            delta = timezone.now() - confirm_email_time
            if delta.total_seconds() < settings.CONFIRMATION_EMAIL_LOCK_TIME:
                raise ValidationError(
                    ValidationError(
                        "Confirmation email already requested",
                        code=SendConfirmationEmailErrorCode.CONFIRMATION_ALREADY_REQUESTED.value,
                    )
                )

        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error},
                code=SendConfirmationEmailErrorCode.INVALID.value,
            )

        return user

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        site = get_site_promise(info.context).get()
        redirect_url = data["redirect_url"]
        user = cls.clean_user(site, redirect_url, info)

        channel = clean_channel(
            data.get("channel"), error_class=SendConfirmationEmailErrorCode
        ).slug
        manager = get_plugin_manager_promise(info.context).get()
        token = default_token_generator.make_token(user)

        send_account_confirmation(
            user,
            redirect_url,
            manager,
            channel_slug=channel,
            token=token,
        )
        user.last_confirm_email_request = timezone.now()
        user.save(update_fields=["last_confirm_email_request", "updated_at"])

        if redirect_url:
            params = urlencode({"email": user.email, "token": token})
            redirect_url = prepare_url(params, redirect_url)

        cls.call_event(
            manager.account_confirmation_requested,
            user,
            channel,
            token,
            redirect_url,
        )

        return SendConfirmationEmail()
