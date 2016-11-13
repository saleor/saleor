from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from ...search.views import paginate_results
from .forms import ModelFilteredSearchForm


@staff_member_required
def search(request):
    form = ModelFilteredSearchForm(data=request.GET or None, load_all=True)
    query = ''
    if form.is_valid():
        results = form.search()
        page = paginate_results(results, request.GET, 25)
        query = form.cleaned_data['q']
    else:
        page = form.no_query_found()
    ctx = {
        'form': form,
        'query': query,
        'results': page,
        'query_string': '?q=%s' % query}
    return render(request, 'dashboard/search/results.html', ctx)
