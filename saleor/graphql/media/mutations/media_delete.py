import graphene

from ....product.error_codes import MediaDeleteErrorCode
from ....product.media import (
    MEDIA_GRAPHQL_TYPE_TO_OWNER_TYPE,
    OWNER_TYPE_TO_UPDATED_EVENT,
)
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_324
from ...core.doc_category import DOC_CATEGORY_MEDIA
from ...core.types import MediaDeleteError
from ...core.utils import WebhookEventInfo
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Media
from .base import BaseMediaMutation


class MediaDelete(BaseMediaMutation):
    media = graphene.Field(Media, description="The deleted media.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the media to delete.")

    class Meta:
        description = (
            "Deletes a media object. The underlying file is not removed from "
            "storage.\n\n"
            "Requires `MANAGE_PRODUCTS` for product, category and collection owners, "
            "and `MANAGE_PAGES` for page owners." + ADDED_IN_324
        )
        doc_category = DOC_CATEGORY_MEDIA
        error_type_class = MediaDeleteError
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.MEDIA_DELETED,
                description="A media object was deleted.",
            ),
        ]

    id_type_to_owner_type = MEDIA_GRAPHQL_TYPE_TO_OWNER_TYPE

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        owner_type, media = cls.get_media(id, MediaDeleteErrorCode)
        owner = media.owner
        media_pk = media.pk
        media.delete()
        # Restore the pk so the response and the event payload can still address it.
        media.pk = media_pk

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(getattr(manager, OWNER_TYPE_TO_UPDATED_EVENT[owner_type]), owner)
        cls.call_event(manager.media_deleted, media)
        return MediaDelete(media=media)
