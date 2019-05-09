from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

__author__ = 'mtford'


def _page(request, query_set):
    paginator = Paginator(query_set, 200)
    page_number = request.GET.get('page')
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    return page
