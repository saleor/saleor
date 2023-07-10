from .....account import models
from .....webhook.event_types import WebhookEventAsyncType
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ...types import Address
from ..base import BaseAddressDelete


class AccountAddressDelete(BaseAddressDelete):
    class Meta:
        auto_permission_message = False
        description = (
            "Delete an address of the logged-in user. Requires one of the following "
            "permissions: MANAGE_USERS, IS_OWNER."
        )
        doc_category = DOC_CATEGORY_USERS
        model = models.Address
        object_type = Address
        error_type_class = AccountError
        error_type_field = "account_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.ADDRESS_DELETED,
                description="An address was deleted.",
            )
        ]
