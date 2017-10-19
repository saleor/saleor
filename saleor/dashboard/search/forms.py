from django.conf import settings
from ...search.backends import get_search_backend
from ...search.forms import SearchForm


class DashboardSearchForm(SearchForm):
    def search(self, queryset_map=None, page=1,
               page_size=settings.DASHBOARD_PAGINATE_BY):
        backend = get_search_backend('dashboard')
        query = self.cleaned_data['q']
        results = backend.search(query, queryset_map=queryset_map,
                                 page=page, page_size=page_size)
        return results
