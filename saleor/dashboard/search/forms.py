from ...search.backends import get_search_backend
from ...search.forms import SearchForm


class DashboardSearchForm(SearchForm):

    def search(self):
        backend = get_search_backend('dashboard')
        query = self.cleaned_data['q']
        results = backend.search(query)
        return results
