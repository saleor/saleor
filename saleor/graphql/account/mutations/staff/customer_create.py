from .....account import models
from .....permission.enums import AccountPermissions
from ....account.types import User
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import AccountError
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
