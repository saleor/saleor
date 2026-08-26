import graphene
from django.core.exceptions import ValidationError

from ....product.error_codes import MediaReorderErrorCode
from ....product.media import (
    GRAPHQL_TYPE_TO_OWNER_TYPE,
    OWNER_TYPE_TO_UPDATED_EVENT,
)
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_324
from ...core.doc_category import DOC_CATEGORY_MEDIA
from ...core.types import MediaReorderError, NonNullList
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Media
from ..utils import update_ordered_media
from .base import BaseMediaMutation

MEDIA_IDS_LIMIT = 100


class MediaReorder(BaseMediaMutation):
    media = NonNullList(Media, description="The media in the new order.")

    class Arguments:
        id = graphene.ID(
            required=True,
            description=(
                "ID of the entity whose media order will be altered. Supported "
                "entities: `Product`, `Category`, `Collection`, `Page`."
            ),
        )
        media_ids = NonNullList(
            graphene.ID,
            required=True,
            description=(
                "IDs of the entity's media in the desired order. Must list every "
                f"media the entity owns. Maximum {MEDIA_IDS_LIMIT} items."
            ),
        )

    class Meta:
        description = (
            "Changes the ordering of an entity's media gallery.\n\n"
            "Requires `MANAGE_PRODUCTS` for product, category and collection owners, "
            "and `MANAGE_PAGES` for page owners." + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_MEDIA
        error_type_class = MediaReorderError

    id_type_to_owner_type = GRAPHQL_TYPE_TO_OWNER_TYPE

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, media_ids
    ):
        if len(media_ids) > MEDIA_IDS_LIMIT:
            raise ValidationError(
                {
                    "media_ids": ValidationError(
                        f"Cannot reorder more than {MEDIA_IDS_LIMIT} media at once.",
                        code=MediaReorderErrorCode.INVALID.value,
                    )
                }
            )

        owner_type, owner = cls.get_owner(info, id, MediaReorderErrorCode)

        if len(media_ids) != owner.media.count():
            raise ValidationError(
                {
                    "media_ids": ValidationError(
                        "Incorrect number of media IDs provided.",
                        code=MediaReorderErrorCode.INVALID.value,
                    )
                }
            )

        ordered_media = []
        for media_id in media_ids:
            _, media = cls.get_media(media_id, MediaReorderErrorCode)
            if getattr(media, f"{owner_type}_id") != owner.pk:
                raise ValidationError(
                    {
                        "media_ids": ValidationError(
                            "Media %(media_id)s does not belong to this entity.",
                            code=MediaReorderErrorCode.NOT_MEDIA_OWNER.value,
                            params={"media_id": media_id},
                        )
                    }
                )
            ordered_media.append(media)

        update_ordered_media(ordered_media, MediaReorderErrorCode)

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(getattr(manager, OWNER_TYPE_TO_UPDATED_EVENT[owner_type]), owner)
        return MediaReorder(media=ordered_media)
