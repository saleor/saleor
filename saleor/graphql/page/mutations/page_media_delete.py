import graphene

from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.types import PageError
from ...plugins.dataloaders import get_plugin_manager_promise
from ....page import models
from ....permission.enums import PagePermissions
from ...core.doc_category import DOC_CATEGORY_PAGES
from ...core.mutations import BaseMutation
from ..types import Page, PageMedia


class PageMediaDelete(BaseMutation):
    page = graphene.Field(Page)
    media = graphene.Field(PageMedia)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a page media to delete.")

    class Meta:
        description = "Deletes a page media."
        doc_category = DOC_CATEGORY_PAGES
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        media_obj = cls.get_node_or_error(info, id, only_type=PageMedia)
        media_id = media_obj.id
        media_obj.delete()
        media_obj.id = media_id
        page = models.Page.objects.prefetched_for_webhook().get(
            pk=media_obj.page_id
        )
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.page_updated, page)
        cls.call_event(manager.page_media_deleted, media_obj)
        page = ChannelContext(node=page, channel_slug=None)
        return PageMediaDelete(page=page, media=media_obj)
