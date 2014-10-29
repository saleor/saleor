from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginate(queryset, paginate_by, page=None):
    paginator = Paginator(queryset, paginate_by)
    try:
        queryset = paginator.page(page)
    except PageNotAnInteger:
        queryset = paginator.page(1)
    except EmptyPage:
        queryset = paginator.page(paginator.num_pages)
    return queryset, paginator
