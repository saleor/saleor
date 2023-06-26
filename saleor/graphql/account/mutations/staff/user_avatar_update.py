from typing import cast

import graphene

from .....account import models
from .....account.error_codes import AccountErrorCode
from .....permission.auth_filters import AuthorizationFilters
from .....thumbnail import models as thumbnail_models
from ....account.types import User
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import AccountError, Upload
from ....core.validators.file import clean_image_file


class UserAvatarUpdate(BaseMutation):
    user = graphene.Field(User, description="An updated user instance.")

    class Arguments:
        image = Upload(
            required=True,
            description="Represents an image file in a multipart request.",
        )

    class Meta:
        description = (
            "Create a user avatar. Only for staff members. This mutation must be sent "
            "as a `multipart` request. More detailed specs of the upload format can be "
            "found here: https://github.com/jaydenseric/graphql-multipart-request-spec"
        )
        doc_category = DOC_CATEGORY_USERS
        error_type_class = AccountError
        error_type_field = "account_errors"
        permissions = (AuthorizationFilters.AUTHENTICATED_STAFF_USER,)

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        user = info.context.user
        user = cast(models.User, user)
        data["image"] = info.context.FILES.get(data["image"])
        image_data = clean_image_file(data, "image", AccountErrorCode)
        if user.avatar:
            user.avatar.delete()
            thumbnail_models.Thumbnail.objects.filter(user_id=user.id).delete()
        user.avatar = image_data
        user.save()

        return UserAvatarUpdate(user=user)
