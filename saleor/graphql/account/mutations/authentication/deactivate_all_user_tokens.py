from typing import cast

from django.utils.crypto import get_random_string

from .....account import models
from .....permission.auth_filters import AuthorizationFilters
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_AUTH
from ....core.mutations import BaseMutation
from ....core.types import AccountError


class DeactivateAllUserTokens(BaseMutation):
    class Meta:
        description = "Deactivate all JWT tokens of the currently authenticated user."
        doc_category = DOC_CATEGORY_AUTH
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_USER,)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /):
        user = info.context.user
        user = cast(models.User, user)
        user.jwt_token_key = get_random_string(length=12)
        user.save(update_fields=["jwt_token_key", "updated_at"])
        return cls()
