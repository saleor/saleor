import graphene
from django.core.exceptions import ValidationError

from saleor.page import models
from saleor.page.error_codes import PageErrorCode
from saleor.permission.enums import PagePermissions
from ..types import Page, PageMedia
from ..utils import ALT_CHAR_LIMIT
from ...channel import ChannelContext
from ...core import ResolveInfo
from ...core.doc_category import DOC_CATEGORY_PAGES
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType, PageError
from ...plugins.dataloaders import get_plugin_manager_promise


class PageMediaUpdateInput(BaseInputObjectType):
    alt = graphene.String(description="Alt text for a page media.")

    class Meta:
        doc_category = DOC_CATEGORY_PAGES


class PageMediaUpdate(BaseMutation):
    page = graphene.Field(Page)
    media = graphene.Field(PageMedia)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a page media to update.")
        input = PageMediaUpdateInput(
            required=True, description="Fields required to update a page media."
        )

    class Meta:
        description = "Updates a page media."
        doc_category = DOC_CATEGORY_PAGES
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        media = cls.get_node_or_error(info, id, only_type=PageMedia)
        page = models.Page.objects.prefetched_for_webhook().get(
            pk=media.page_id
        )
        alt = input.get("alt")
        if alt is not None:
            if len(alt) > ALT_CHAR_LIMIT:
                raise ValidationError(
                    {
                        "input": ValidationError(
                            f"Alt field exceeds the character "
                            f"limit of {ALT_CHAR_LIMIT}.",
                            code=PageErrorCode.INVALID.value,
                        )
                    }
                )
            media.alt = alt
            media.save(update_fields=["alt"])
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.page_updated, page)
        cls.call_event(manager.page_media_updated, media)
        page = ChannelContext(node=page, channel_slug=None)
        return PageMediaUpdate(page=page, media=media)
