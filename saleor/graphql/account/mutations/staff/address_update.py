from .....account import models
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import Address
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import AccountError
from ....core.utils import WebhookEventInfo
from ...mixins import AddressMetadataMixin
from ..base import BaseAddressUpdate


class AddressUpdate(AddressMetadataMixin, BaseAddressUpdate):
    class Meta:
        description = "Updates an address."
        doc_category = DOC_CATEGORY_USERS
        model = models.Address
        object_type = Address
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.ADDRESS_UPDATED,
                description="An address was updated.",
            ),
        ]
