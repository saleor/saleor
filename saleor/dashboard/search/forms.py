from ...search.backends import picker
from ...search.forms import SearchForm


class DashboardSearchForm(SearchForm):
    def search(self):
        query = self.cleaned_data['q']
        search = picker.pick_dashboard_backend()
        return search(query)
