import graphene

from ...page import models
from ..utils import filter_by_query_param
from .types import Page

PAGE_SEARCH_FIELDS = ('content', 'slug', 'title')


def resolve_page(info, id=None, slug=None):
    assert id or slug, 'No page ID or slug provided.'
    if slug is not None:
        try:
            return models.Page.objects.get(slug=slug)
        except models.Page.DoesNotExist:
            return None
    return graphene.Node.get_node_from_global_id(info, id, Page)


def resolve_pages(info, query):
    user = info.context.user
    if user.has_perm('page.manage_pages'):
        qs = models.Page.objects.all()
    else:
        qs = models.Page.objects.public()
    qs = filter_by_query_param(qs, query, PAGE_SEARCH_FIELDS)
    return qs.distinct()
