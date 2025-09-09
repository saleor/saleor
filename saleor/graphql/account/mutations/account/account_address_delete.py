from .....account import models
from .....webhook.event_types import WebhookEventAsyncType
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import AccountError
from ....directives import doc, webhook_events
from ...types import Address
from ..base import BaseAddressDelete


@doc(category=DOC_CATEGORY_USERS)
@webhook_events(async_events={WebhookEventAsyncType.ADDRESS_DELETED})
class AccountAddressDelete(BaseAddressDelete):
    """Deletes an address of the logged-in user.

    Requires one of the following permissions: MANAGE_USERS, or IS_OWNER.
    """

    class Meta:
        auto_permission_message = False
        model = models.Address
        object_type = Address
        error_type_class = AccountError
        error_type_field = "account_errors"
