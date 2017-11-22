from ...search.forms import SearchForm
from ...search.backends import elasticsearch_dashboard


class DashboardSearchForm(SearchForm):
    def search(self):
        query = self.cleaned_data['q']
        return elasticsearch_dashboard.search(query)
