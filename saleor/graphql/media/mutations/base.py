from django.core.exceptions import ValidationError
from graphql.error import GraphQLError

from ....permission.enums import BasePermissionEnum
from ....product import models
from ....product.media import (
    GRAPHQL_TYPE_TO_OWNER_TYPE,
    MEDIA_GRAPHQL_TYPE_TO_OWNER_TYPE,
    MEDIA_OWNER_PERMISSION_MAP,
    OWNER_TYPE_TO_MODEL,
)
from ...core import ResolveInfo
from ...core.mutations import BaseMutation
from ...core.utils import from_global_id_or_error


def _owner_type_from_global_id(
    global_id: str | None, type_to_owner_type: dict[str, str]
) -> str | None:
    """Return the media owner type a global ID points at, or None if unsupported."""
    if not global_id:
        return None
    try:
        type_name, _ = from_global_id_or_error(global_id)
    except GraphQLError:
        return None
    return type_to_owner_type.get(type_name)


class BaseMediaMutation(BaseMutation):
    """Resolve the required permission from the owner encoded in the global ID.

    The concrete mutations differ only in whether their `id` argument points at the
    owner (`mediaCreate`, `mediaReorder`) or at the media itself (`mediaUpdate`,
    `mediaDelete`).
    """

    class Meta:
        abstract = True

    # Maps the GraphQL type name in the `id` argument to a media owner type.
    id_type_to_owner_type: dict[str, str] = {}

    @classmethod
    def get_owner_type(cls, data: dict) -> str | None:
        return _owner_type_from_global_id(data.get("id"), cls.id_type_to_owner_type)

    @classmethod
    def check_permissions(
        cls, context, permissions=None, require_all_permissions=False, **data
    ):
        owner_type = cls.get_owner_type(data.get("data") or {})
        if owner_type is None:
            # The ID does not name a supported owner. Let the mutation run so it can
            # raise a precise validation error instead of a misleading denial; it
            # cannot reach any object either way.
            return True
        permission: BasePermissionEnum = MEDIA_OWNER_PERMISSION_MAP[owner_type]
        return super().check_permissions(
            context, [permission], require_all_permissions, **data
        )

    @classmethod
    def get_owner(cls, info: ResolveInfo, owner_id: str, error_code_enum):
        """Resolve the owner entity from its global ID."""
        owner_type = _owner_type_from_global_id(owner_id, GRAPHQL_TYPE_TO_OWNER_TYPE)
        if owner_type is None:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Media can only be attached to a Product, Category, "
                        "Collection or Page.",
                        code=error_code_enum.INVALID.value,
                    )
                }
            )
        _, owner_pk = from_global_id_or_error(owner_id)
        owner = (
            OWNER_TYPE_TO_MODEL[owner_type].objects.filter(pk=owner_pk).first()  # type: ignore[attr-defined]
        )
        if owner is None:
            raise ValidationError(
                {
                    "id": ValidationError(
                        f"Couldn't resolve to an object: {owner_id}",
                        code=error_code_enum.NOT_FOUND.value,
                    )
                }
            )
        return owner_type, owner

    @classmethod
    def get_media(
        cls, media_id: str, error_code_enum
    ) -> tuple[str, models.ProductMedia]:
        """Resolve a media row and its owner type from an owner-typed global ID."""
        owner_type = _owner_type_from_global_id(
            media_id, MEDIA_GRAPHQL_TYPE_TO_OWNER_TYPE
        )
        if owner_type is None:
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Expected a ProductMedia, CategoryMedia, CollectionMedia "
                        "or PageMedia ID.",
                        code=error_code_enum.INVALID.value,
                    )
                }
            )
        _, media_pk = from_global_id_or_error(media_id)
        media = (
            models.ProductMedia.objects.filter(pk=media_pk)
            .exclude(**{f"{owner_type}_id": None})
            .first()
        )
        if media is None:
            raise ValidationError(
                {
                    "id": ValidationError(
                        f"Couldn't resolve to an object: {media_id}",
                        code=error_code_enum.NOT_FOUND.value,
                    )
                }
            )
        return owner_type, media
