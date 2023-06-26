from .....account import models
from .....permission.enums import AccountPermissions
from ....account.types import Address
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import AccountError
from ..base import BaseAddressUpdate


class AddressUpdate(BaseAddressUpdate):
    class Meta:
        description = "Updates an address."
        doc_category = DOC_CATEGORY_USERS
        model = models.Address
        object_type = Address
        permissions = (AccountPermissions.MANAGE_USERS,)
        error_type_class = AccountError
        error_type_field = "account_errors"
