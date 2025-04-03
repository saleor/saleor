from urllib.parse import urlencode

from django.contrib.auth.tokens import default_token_generator

from .....account import events as account_events
from .....account import models
from .....account.notifications import send_set_password_notification
from .....account.search import prepare_user_search_document_value
from .....core.tracing import traced_atomic_transaction
from .....core.utils.url import prepare_url
from .....permission.enums import AccountPermissions
from .....plugins.manager import PluginsManager
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import User
from ....channel.utils import clean_channel, validate_channel
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.enums import AccountErrorCode
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ....plugins.dataloaders import get_plugin_manager_promise
from ..base import BaseCustomerCreate


class CustomerCreate(BaseCustomerCreate):
    class Meta:
        description = "Creates a new customer."
        doc_category = DOC_CATEGORY_USERS
        exclude = ["password"]
        model = models.User
        object_type = User
        permissions = (AccountPermissions.MANAGE_USERS,)
        support_meta_field = True
        support_private_meta_field = True
        error_type_class = AccountError
        error_type_field = "account_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_CREATED,
                description="A new customer account was created.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_METADATA_UPDATED,
                description="Optionally called when customer's metadata was updated.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.NOTIFY_USER,
                description="A notification for setting the password.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.ACCOUNT_SET_PASSWORD_REQUESTED,
                description="Setting a new password for the account is requested.",
            ),
        ]

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        manager = get_plugin_manager_promise(info.context).get()

        cls.save_default_addresses(
            cleaned_input=cleaned_input, user_instance=instance, save_user=True
        )

        instance.search_document = prepare_user_search_document_value(instance)
        instance.save(update_fields=["search_document"])

        cls.call_event(manager.customer_created, instance)
        account_events.customer_account_created_event(user=instance)

        if redirect_url := cleaned_input.get("redirect_url"):
            cls._process_sending_password(
                redirect_url=redirect_url,
                instance=instance,
                channel_slug_from_input=cleaned_input.get("channel"),
                plugins_manager=manager,
            )

    @classmethod
    def _process_sending_password(
        cls,
        *,
        redirect_url: str,
        instance: models.User,
        plugins_manager: PluginsManager,
        channel_slug_from_input: str,
    ):
        channel_slug = channel_slug_from_input

        if not instance.is_staff:
            channel_slug = clean_channel(
                channel_slug, error_class=AccountErrorCode, allow_replica=False
            ).slug
        elif channel_slug is not None:
            channel_slug = validate_channel(
                channel_slug, error_class=AccountErrorCode
            ).slug

        send_set_password_notification(
            redirect_url,
            instance,
            plugins_manager,
            channel_slug,
        )
        token = default_token_generator.make_token(instance)
        params = urlencode({"email": instance.email, "token": token})

        cls.call_event(
            plugins_manager.account_set_password_requested,
            instance,
            channel_slug,
            token,
            prepare_url(params, redirect_url),
        )
