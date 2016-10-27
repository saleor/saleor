import datetime
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator, InvalidPage
from django.http import Http404
from django.shortcuts import render
from haystack.forms import SearchForm

from ..order.models import Order
from ..product.models import Product
from ..userprofile.models import User


def paginate_results(results, get_data, paginate_by=25):
    paginator = Paginator(results, paginate_by)
    page_number = get_data.get('page', 1)
    try:
        page = paginator.page(page_number)
    except InvalidPage:
        raise Http404("No such page!")
    return page


def search(request):
    form = SearchForm(data=request.GET or None, load_all=True)
    today = datetime.date.today()
    if form.is_valid():
        results = form.search().models(Product)
        results = results.filter_or(available_on__lte=today)
        page = paginate_results(results, request.GET, 25)
    else:
        page = form.no_query_found()
    query = form.cleaned_data['q']
    ctx = {
        'query': query,
        'results': page,
        'query_string': '?q=%s' % query}
    return render(request, 'search/results.html', ctx)


@staff_member_required
def dashboard_search(request):
    form = SearchForm(data=request.GET or None, load_all=True)
    if form.is_valid():
        results = form.search().models(Order, Product, User)
        page = paginate_results(results, request.GET, 25)
    else:
        page = form.no_query_found()
    query = form.cleaned_data['q']
    ctx = {
        'query': query,
        'results': page,
        'query_string': '?q=%s' % query}
    return render(request, 'search/dashboard_results.html', ctx)
