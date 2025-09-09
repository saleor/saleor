from .....account import models
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....account.types import Address
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import AccountError
from ....directives import doc, webhook_events
from ..base import BaseAddressDelete


@doc(category=DOC_CATEGORY_USERS)
@webhook_events({WebhookEventAsyncType.ADDRESS_DELETED})
class AddressDelete(BaseAddressDelete):
    """Deletes an address."""

    class Meta:
        model = models.Address
        object_type = Address
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"
