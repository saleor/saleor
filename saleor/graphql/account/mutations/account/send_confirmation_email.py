from typing import cast

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone

from .....account import models
from .....account.error_codes import SendConfirmationEmailErrorCode
from .....account.notifications import send_account_confirmation
from .....core.utils.url import validate_storefront_url
from .....permission.auth_filters import AuthorizationFilters
from ....account.types import User
from ....channel.utils import clean_channel
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import SendConfirmationEmailError
from ....plugins.dataloaders import get_plugin_manager_promise
from ....site.dataloaders import get_site_promise


class SendConfirmationEmail(BaseMutation):
    user = graphene.Field(User, description="An user instance.")

    class Arguments:
        redirect_url = graphene.String(
            required=True,
            description=(
                "Base of frontend URL that will be needed to create confirmation "
                "URL."
            ),
        )
        channel = graphene.String(
            description=(
                "Slug of a channel which will be used for notify user. Optional when "
                "only one channel exists."
            )
        )

    class Meta:
        description = "Sends an email with confirmation link."
        doc_category = DOC_CATEGORY_USERS
        error_type_class = SendConfirmationEmailError
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)

    @classmethod
    def clean_user(cls, site, redirect_url, info: ResolveInfo):
        if not site.settings.enable_account_confirmation_by_email:
            raise ValidationError(
                ValidationError(
                    "Email confirmation is disabled",
                    code=SendConfirmationEmailErrorCode.CONFIRMATION_DISABLED.value,
                )
            )

        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error},
                code=SendConfirmationEmailErrorCode.INVALID.value,
            )

        user = info.context.user
        user = cast(models.User, user)

        if user.is_confirmed:
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

        send_account_confirmation(
            user,
            redirect_url,
            manager,
            channel_slug=channel,
        )
        user.last_confirm_email_request = timezone.now()
        user.save(update_fields=["last_confirm_email_request", "updated_at"])

        return SendConfirmationEmail(user)