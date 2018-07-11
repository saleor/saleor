from ...page import models
from ..utils import filter_by_query_param, get_node
from .types import Page

PAGE_SEARCH_FIELDS = ('content', 'slug', 'title')


def resolve_page(info, id=None, slug=None):
    assert id or slug, 'No page ID or slug provided.'
    if slug is not None:
        return models.Page.objects.get(slug=slug)
    return get_node(info, id, only_type=Page)


def resolve_pages(user, query):
    if user.is_authenticated and user.is_active and user.is_staff:
        # FIXME: check page permissions
        queryset = models.Page.objects.all().distinct()
        queryset = filter_by_query_param(queryset, query, PAGE_SEARCH_FIELDS)
        return queryset
    queryset = models.Page.objects.public().distinct()
    queryset = filter_by_query_param(queryset, query, PAGE_SEARCH_FIELDS)
    return queryset
