import graphene

from ...page import models
from ..utils import filter_by_query_param

PAGE_SEARCH_FIELDS = ("content", "slug", "title")


def resolve_page(info, page_global_id=None, slug=None):
    assert page_global_id or slug, "No page ID or slug provided."
    user = info.context.user

    if slug is not None:
        page = models.Page.objects.visible_to_user(user).filter(slug=slug).first()
    else:
        _type, page_pk = graphene.Node.from_global_id(page_global_id)
        page = models.Page.objects.visible_to_user(user).filter(pk=page_pk).first()
    return page


def resolve_pages(info, query):
    user = info.context.user
    qs = models.Page.objects.visible_to_user(user)
    return filter_by_query_param(qs, query, PAGE_SEARCH_FIELDS)
