from .....account import models
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import User
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
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
        ]
