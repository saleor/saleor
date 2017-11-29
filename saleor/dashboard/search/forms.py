from __future__ import unicode_literals

from ...search.backends import elasticsearch_dashboard
from ...search.forms import SearchForm


class DashboardSearchForm(SearchForm):
    def search(self):
        query = self.cleaned_data['q']
        return elasticsearch_dashboard.search(query)
