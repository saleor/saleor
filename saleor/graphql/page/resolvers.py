from ...channel.models import Channel
from ...page import models
from ..core.context import ChannelQsContext, get_database_connection_name
from ..core.utils import from_global_id_or_error
from ..core.validators import validate_one_of_args_is_in_query
from ..utils import get_user_or_app_from_context
from .types import Page


def resolve_page(info, global_page_id=None, slug=None, slug_language_code=None):
    validate_one_of_args_is_in_query("id", global_page_id, "slug", slug)
    requestor = get_user_or_app_from_context(info.context)

    if slug is not None:
        if slug_language_code is None:
            page = (
                models.Page.objects.using(get_database_connection_name(info.context))
                .visible_to_user(requestor)
                .filter(slug=slug)
                .first()
            )
        else:
            page = (
                models.Page.objects.using(get_database_connection_name(info.context))
                .visible_to_user(requestor)
                .filter(
                    translations__slug=slug,
                    translations__language_code=slug_language_code,
                )
                .first()
            )
    else:
        _type, page_pk = from_global_id_or_error(global_page_id, Page)
        page = (
            models.Page.objects.using(get_database_connection_name(info.context))
            .visible_to_user(requestor)
            .filter(pk=page_pk)
            .first()
        )
    return page


def resolve_pages(
    info, channel_slug: str | None = None, channel: Channel | None = None
) -> ChannelQsContext[models.Page]:
    requestor = get_user_or_app_from_context(info.context)
    if channel is None and channel_slug is not None:
        # If channel is provided but not found, return None
        page_qs = models.Page.objects.none()
    else:
        page_qs = models.Page.objects.using(
            get_database_connection_name(info.context)
        ).visible_to_user(requestor)
    return ChannelQsContext(qs=page_qs, channel_slug=channel_slug)


def resolve_page_type(info, id):
    return (
        models.PageType.objects.using(get_database_connection_name(info.context))
        .filter(id=id)
        .first()
    )


def resolve_page_types(info):
    return models.PageType.objects.using(
        get_database_connection_name(info.context)
    ).all()
