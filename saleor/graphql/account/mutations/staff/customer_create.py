from urllib.parse import urlencode

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from .....account import events as account_events
from .....account import models
from .....account.notifications import send_set_password_notification
from .....account.search import prepare_user_search_document_value
from .....core.tokens import token_generator
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
from ..base import BILLING_ADDRESS_FIELD, SHIPPING_ADDRESS_FIELD, BaseCustomerCreate


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
    def _save(cls, instance):
        """Prevent race condition when saving customer.

        This is a hacky solution that catches DB error, to deduct that entity was
        created before.

        Normally we would use get_or_create here, but it will lose reference -
        get_or_create returns new instance of model, but original "instance" is being
        returned in mutation.

        This limitation comes from the Base/Model mutation. We can solve this e.g. by
        returning actual instance from save()

        https://linear.app/saleor/issue/EXT-2162
        """
        with transaction.atomic():
            try:
                with transaction.atomic():
                    instance.save()
            except IntegrityError:
                try:
                    # Verify if object already exists in DB.
                    # If yes, it means we have a race-condition
                    # This eventually leads to ValidationError because this user
                    # already exists
                    models.User.objects.get(email=instance.email)

                    raise ValidationError(
                        {
                            # This validation error mimics built-in validation error
                            # So graphQL response is the same
                            "email": ValidationError(
                                "User with this Email already exists.",
                                code=AccountErrorCode.UNIQUE.value,
                            )
                        }
                    )
                except instance.DoesNotExist:
                    pass
                raise

    @classmethod
    @traced_atomic_transaction()
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        addresses_to_set_on_user = []
        if default_shipping_address := cleaned_input.get(SHIPPING_ADDRESS_FIELD):
            addresses_to_set_on_user.append(default_shipping_address)
            default_shipping_address.save()
        if default_billing_address := cleaned_input.get(BILLING_ADDRESS_FIELD):
            addresses_to_set_on_user.append(default_billing_address)
            default_billing_address.save()

        cls._save(instance)

        if addresses_to_set_on_user:
            instance.addresses.set(addresses_to_set_on_user)

        manager = get_plugin_manager_promise(info.context).get()

        instance.search_document = prepare_user_search_document_value(instance)
        instance.save()

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
        token = token_generator.make_token(instance)
        params = urlencode({"email": instance.email, "token": token})

        cls.call_event(
            plugins_manager.account_set_password_requested,
            instance,
            channel_slug,
            token,
            prepare_url(params, redirect_url),
        )
