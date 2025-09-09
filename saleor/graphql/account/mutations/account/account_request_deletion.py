from typing import cast
from urllib.parse import urlencode

import graphene
from django.core.exceptions import ValidationError

from .....account import notifications
from .....account.error_codes import AccountErrorCode
from .....account.models import User
from .....core.tokens import account_delete_token_generator
from .....core.utils.url import prepare_url, validate_storefront_url
from .....permission.auth_filters import AuthorizationFilters
from .....webhook.event_types import WebhookEventAsyncType
from ....channel.utils import clean_channel
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....directives import doc, webhook_events
from ....plugins.dataloaders import get_plugin_manager_promise


@doc(category=DOC_CATEGORY_USERS)
@webhook_events(
    async_events={
        WebhookEventAsyncType.NOTIFY_USER,
        WebhookEventAsyncType.ACCOUNT_DELETE_REQUESTED,
    }
)
class AccountRequestDeletion(BaseMutation):
    """Sends an email with the account removal link for the logged-in user."""

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
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, channel=None, redirect_url
    ):
        user = cast(User, info.context.user)
        try:
            validate_storefront_url(redirect_url)
        except ValidationError as e:
            raise ValidationError(
                {"redirect_url": e}, code=AccountErrorCode.INVALID.value
            ) from e
        channel_slug = clean_channel(
            channel, error_class=AccountErrorCode, allow_replica=False
        ).slug
        manager = get_plugin_manager_promise(info.context).get()
        token = account_delete_token_generator.make_token(user)

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
