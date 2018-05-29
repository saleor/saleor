from ...page import models
from ..utils import filter_by_query_param

PAGE_SEARCH_FIELDS = ('content', 'slug', 'title')


def resolve_pages(user, query):
    if user.is_authenticated and user.is_active and user.is_staff:
        queryset = models.Page.objects.all().distinct()
        queryset = filter_by_query_param(queryset, query, PAGE_SEARCH_FIELDS)
        return queryset
    queryset = models.Page.objects.public().distinct()
    queryset = filter_by_query_param(queryset, query, PAGE_SEARCH_FIELDS)
    return queryset
