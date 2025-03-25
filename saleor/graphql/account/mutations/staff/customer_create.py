from .....account import events as account_events
from .....account import models
from .....account.search import prepare_user_search_document_value
from .....core.tracing import traced_atomic_transaction
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import User
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
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
    @traced_atomic_transaction()
    def save(cls, info: ResolveInfo, instance, cleaned_input):
        default_shipping_address = cleaned_input.get(SHIPPING_ADDRESS_FIELD)
        manager = get_plugin_manager_promise(info.context).get()

        if default_shipping_address:
            default_shipping_address.save()
            instance.default_shipping_address = default_shipping_address

        default_billing_address = cleaned_input.get(BILLING_ADDRESS_FIELD)

        if default_billing_address:
            default_billing_address.save()
            instance.default_billing_address = default_billing_address

        super().save(info, instance, cleaned_input)
        if default_billing_address:
            instance.addresses.add(default_billing_address)
        if default_shipping_address:
            instance.addresses.add(default_shipping_address)

        instance.search_document = prepare_user_search_document_value(instance)
        instance.save(update_fields=["search_document", "updated_at"])

        cls.call_event(manager.customer_created, instance)
        account_events.customer_account_created_event(user=instance)

        if redirect_url := cleaned_input.get("redirect_url"):
            cls.process_account_confirmation(
                redirect_url=redirect_url,
                instance=instance,
                channel_slug_from_input=cleaned_input.get("channel"),
                plugins_manager=manager,
            )
