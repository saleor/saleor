from typing import cast

import graphene

from .....account import models
from .....permission.auth_filters import AuthorizationFilters
from .....thumbnail import models as thumbnail_models
from ....account.types import User
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import AccountError


class UserAvatarDelete(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Meta:
        description = "Deletes a user avatar. Only for staff members."
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_STAFF_USER,)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /):
        user = info.context.user
        user = cast(models.User, user)
        user.avatar.delete()
        thumbnail_models.Thumbnail.objects.filter(user_id=user.id).delete()
        return UserAvatarDelete(user=user)
