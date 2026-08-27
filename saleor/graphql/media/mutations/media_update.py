import graphene
from django.core.exceptions import ValidationError

from ....product.error_codes import MediaUpdateErrorCode
from ....product.media import (
    ALT_CHAR_LIMIT,
    MEDIA_GRAPHQL_TYPE_TO_OWNER_TYPE,
    OWNER_TYPE_TO_UPDATED_EVENT,
)
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_324
from ...core.doc_category import DOC_CATEGORY_MEDIA
from ...core.types import BaseInputObjectType, MediaUpdateError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Media
from .base import BaseMediaMutation


class MediaUpdateInput(BaseInputObjectType):
    alt = graphene.String(
        description=f"Alt text for the media. Maximum {ALT_CHAR_LIMIT} characters."
    )

    class Meta:
        description = "Fields required to update a media object." + ADDED_IN_324
        doc_category = DOC_CATEGORY_MEDIA


class MediaUpdate(BaseMediaMutation):
    media = graphene.Field(Media, description="The updated media.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the media to update.")
        input = MediaUpdateInput(
            required=True, description="Fields required to update the media object."
        )

    class Meta:
        description = (
            "Updates a media object.\n\n"
            "Requires `MANAGE_PRODUCTS` for product, category and collection owners, "
            "and `MANAGE_PAGES` for page owners." + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_MEDIA
        error_type_class = MediaUpdateError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.MEDIA_UPDATED,
                description="A media object was updated.",
            ),
        ]

    id_type_to_owner_type = MEDIA_GRAPHQL_TYPE_TO_OWNER_TYPE

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        owner_type, media = cls.get_media(id, MediaUpdateErrorCode)
        alt = input.get("alt")
        if alt is not None:
            if len(alt) > ALT_CHAR_LIMIT:
                raise ValidationError(
                    {
                        "input": ValidationError(
                            "Alt field exceeds the character limit of "
                            f"{ALT_CHAR_LIMIT}.",
                            code=MediaUpdateErrorCode.INVALID.value,
                        )
                    }
                )
            media.alt = alt
            media.save(update_fields=["alt"])

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(
            getattr(manager, OWNER_TYPE_TO_UPDATED_EVENT[owner_type]), media.owner
        )
        cls.call_event(manager.media_updated, media)
        return MediaUpdate(media=media)
