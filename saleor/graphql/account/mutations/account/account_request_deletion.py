from urllib.parse import urlencode

import graphene
from django.core.exceptions import ValidationError

from .....account import notifications
from .....account.error_codes import AccountErrorCode
from .....core.tokens import account_delete_token_generator
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


class AccountRequestDeletion(BaseMutation):
    class Arguments:
        redirect_url = graphene.String(
            required=True,
            description=(
                "URL of a view where users should be redirected to "
                "delete their account. URL in RFC 1808 format."
            ),
        )
        channel = graphene.String(
            description=(
                "Slug of a channel which will be used to notify users. Optional when "
                "only one channel exists."
            )
        )

    class Meta:
        description = (
            "Sends an email with the account removal link for the logged-in user."
        )
        doc_category = DOC_CATEGORY_USERS
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)
        error_type_class = AccountError
        error_type_field = "account_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for account delete request.",
            )
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, channel=None, redirect_url
    ):
        user = info.context.user
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as error:
            raise ValidationError(
                {"redirect_url": error}, code=AccountErrorCode.INVALID.value
            )
        channel_slug = clean_channel(channel, error_class=AccountErrorCode).slug
        manager = get_plugin_manager_promise(info.context).get()
        token = account_delete_token_generator.make_token(user)  # type: ignore

        # Notifications will be deprecated in the future
        notifications.send_account_delete_confirmation_notification(
            redirect_url, user, manager, channel_slug=channel_slug, token=token
        )
        params = urlencode({"token": token})
        delete_url = prepare_url(params, redirect_url)

        cls.call_event(
            manager.account_delete_requested,
            user,
            channel_slug,
            token,
            delete_url,
        )

        return AccountRequestDeletion()
