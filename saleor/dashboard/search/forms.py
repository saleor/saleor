from ...search.forms import SearchForm
from ...search.backends import newelastic


class DashboardSearchForm(SearchForm):
    def search(self, queryset_map=None):
        query = self.cleaned_data['q']
        results = newelastic.SearchBackend.search(
            query, queryset_map=queryset_map)
        return results
