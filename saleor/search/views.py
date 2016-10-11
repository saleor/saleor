from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.shortcuts import render
from haystack.forms import SearchForm

from ..order.models import Order
from ..product.models import Product
from ..userprofile.models import User


def search_for_model(request, models):
    form = SearchForm(data=request.GET or None, load_all=True)
    paginate_by = 25
    if form.is_valid():
        results = form.search().models(*models)
        paginator = Paginator(results, paginate_by)
        page_number = request.GET.get('page', 1)
        try:
            page = paginator.page(page_number)
        except InvalidPage:
            raise Http404("No such page!")
    else:
        page = form.no_query_found()
    return {'page': page, 'query': form.cleaned_data['q']}


def search(request):
    search_data = search_for_model(request, models=[Product])
    ctx = {
        'query': search_data['query'],
        'results': search_data['page'],
        'query_string': '?q=%s' % search_data['query']}
    return render(request, 'search/results.html', ctx)


@staff_member_required
def dashboard_search(request):
    search_data = search_for_model(request, models=[Order, Product, User])
    ctx = {
        'query': search_data['query'],
        'results': search_data['page'],
        'query_string': '?q=%s' % search_data['query']}
    return render(request, 'search/dashboard_results.html', ctx)
